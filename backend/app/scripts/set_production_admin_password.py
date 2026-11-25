"""Set a production administrator password through a hidden terminal prompt.

This is the safe recovery path when the operator has an existing administrator
session but cannot reach the database credentials. It talks to the public HTTPS
API only, never prints a password, and deletes the temporary recovery file after
a successful change.

Run from the ``backend`` directory:

    python -m app.scripts.set_production_admin_password --email admin@college.edu

If ``--current-password-file`` exists (default
``~/.facultyinsight-admin-recovery.txt``), the current password is read from it
instead of being typed. The new password is always entered with ``getpass``.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

from fastapi import HTTPException

from app.core.security import validate_password_strength

DEFAULT_BASE_URL = "https://faculty-feedback-system-blush.vercel.app"
DEFAULT_SECRET_FILE = Path.home() / ".facultyinsight-admin-recovery.txt"


def _read_password_file(path: Path) -> str | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^password=(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else None


def _prompt(label: str) -> str:
    value = getpass.getpass(label)
    if not value:
        raise SystemExit(f"{label.strip()} cannot be empty.")
    return value


def _validate(password: str) -> None:
    try:
        validate_password_strength(password)
    except HTTPException as exc:
        raise SystemExit(f"Password rejected: {exc.detail}") from exc


def _call(
    base_url: str,
    method: str,
    path: str,
    token: str | None = None,
    body: dict | None = None,
) -> tuple[int, object]:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(base_url + path, data=data, method=method)
    request.add_header("Accept", "application/json")
    if data is not None:
        request.add_header("Content-Type", "application/json")
    if token:
        request.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read().decode()
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            return exc.code, json.loads(raw) if raw else None
        except json.JSONDecodeError:
            return exc.code, raw


def _detail(payload: object) -> str:
    return payload.get("detail", "") if isinstance(payload, dict) else str(payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Change a FacultyInsight administrator password using a hidden prompt."
    )
    parser.add_argument("--email", required=True, help="Administrator email address.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Production base URL.")
    parser.add_argument(
        "--current-password-file",
        type=Path,
        default=DEFAULT_SECRET_FILE,
        help="Optional file containing the current temporary password.",
    )
    args = parser.parse_args(argv)

    current_password = _read_password_file(args.current_password_file)
    if current_password is None:
        current_password = _prompt("Current administrator password: ")

    new_password = _prompt("New administrator password: ")
    _validate(new_password)
    confirm_password = _prompt("Confirm new password: ")
    if new_password != confirm_password:
        raise SystemExit("Passwords do not match. Nothing was changed.")

    status, session = _call(
        args.base_url,
        "POST",
        "/api/auth/admin/login",
        body={"email": args.email, "password": current_password},
    )
    if status != 200:
        raise SystemExit(f"Sign-in failed ({status}): {_detail(session)}")
    token = session["access_token"]
    print("PASS current administrator password accepted.")

    status, payload = _call(
        args.base_url,
        "POST",
        "/api/auth/change-password",
        token,
        {
            "current_password": current_password,
            "new_password": new_password,
            "confirm_password": confirm_password,
        },
    )
    if status != 200:
        raise SystemExit(f"Password change failed ({status}): {_detail(payload)}")
    print("PASS password changed.")

    status, session = _call(
        args.base_url,
        "POST",
        "/api/auth/admin/login",
        body={"email": args.email, "password": new_password},
    )
    if status != 200:
        raise SystemExit(f"New password verification failed ({status}): {_detail(session)}")
    new_token = session["access_token"]
    print("PASS new password signs in.")

    status, me = _call(args.base_url, "GET", "/api/auth/me", new_token)
    if status != 200 or me.get("role") != "admin":
        raise SystemExit(f"Identity verification failed ({status}).")
    print("PASS administrator identity verified.")

    status, _ = _call(args.base_url, "GET", "/api/admin/dashboard", new_token)
    if status != 200:
        raise SystemExit(f"Administrator dashboard check failed ({status}).")
    print("PASS administrator dashboard reachable.")

    if args.current_password_file.exists():
        args.current_password_file.unlink()
        print("Temporary recovery file removed.")
    print("Done. Use the new password for future administrator sign-ins.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
