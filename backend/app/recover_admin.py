"""Operator-only administrator recovery.

This command is the secure recovery path when nobody can sign in as an
administrator. It requires direct access to the database credentials (the same
``DATABASE_URL`` the API uses) and therefore cannot be triggered by the public
website. It never prints a password or password hash and never reopens public
administrator registration.

Run from the ``backend`` directory:

    python -m app.recover_admin --list
    python -m app.recover_admin --email admin@college.edu --name "Administrator"
    python -m app.recover_admin --email admin@college.edu --reset

``--reset`` asks for an explicit ``RESET`` confirmation before changing an
existing administrator's password.
"""

from __future__ import annotations

import argparse
import getpass
import sys

import psycopg
from fastapi import HTTPException
from psycopg.errors import UniqueViolation

from app.core.security import hash_password, normalize_email, validate_password_strength
from app.db import connect


class RecoveryError(Exception):
    """A safe, user-facing recovery failure."""


def list_admins(conn: psycopg.Connection) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT admin_id, name, email, is_active, created_at FROM admins ORDER BY admin_id"
        )
        return list(cur.fetchall())


def create_admin(
    conn: psycopg.Connection, *, name: str, email: str, password: str
) -> int:
    normalized = normalize_email(email)
    validate_password_strength(password)
    password_hash = hash_password(password)
    try:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute("SELECT admin_id FROM admins WHERE email = %s", (normalized,))
                if cur.fetchone() is not None:
                    raise RecoveryError(
                        "An administrator with this email already exists. "
                        "Use --reset to change its password."
                    )
                cur.execute(
                    """
                    INSERT INTO admins (name, email, password_hash)
                    VALUES (%s, %s, %s) RETURNING admin_id
                    """,
                    (name.strip(), normalized, password_hash),
                )
                return cur.fetchone()["admin_id"]
    except UniqueViolation as exc:
        raise RecoveryError("An administrator with this email already exists.") from exc


def reset_admin_password(conn: psycopg.Connection, *, email: str, password: str) -> int:
    normalized = normalize_email(email)
    validate_password_strength(password)
    password_hash = hash_password(password)
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE admins SET password_hash = %s WHERE email = %s RETURNING admin_id",
                (password_hash, normalized),
            )
            row = cur.fetchone()
    if row is None:
        raise RecoveryError("No administrator account was found for this email.")
    return row["admin_id"]


def _prompt_password() -> str:
    password = getpass.getpass("New administrator password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        raise RecoveryError("Passwords do not match.")
    return password


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create or reset an administrator without public registration."
    )
    parser.add_argument("--list", action="store_true", help="List administrator emails.")
    parser.add_argument("--email", help="Administrator email address.")
    parser.add_argument("--name", default="Administrator", help="Display name for a new admin.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset the password of an existing administrator (explicit confirmation required).",
    )
    args = parser.parse_args(argv)

    try:
        conn = connect()
    except psycopg.OperationalError:
        print(
            "Recovery failed: the database is unavailable. Check DATABASE_URL and try again.",
            file=sys.stderr,
        )
        return 1
    try:
        if args.list:
            rows = list_admins(conn)
            if not rows:
                print("No administrator accounts exist.")
                return 0
            for row in rows:
                state = "active" if row["is_active"] else "inactive"
                print(f"{row['admin_id']}: {row['email']} ({state})")
            return 0

        if not args.email:
            parser.error("--email is required unless --list is used.")

        password = _prompt_password()
        if args.reset:
            confirmation = input(
                "Type RESET to confirm changing this administrator's password: "
            )
            if confirmation.strip() != "RESET":
                print("Aborted. No password was changed.")
                return 1
            admin_id = reset_admin_password(conn, email=args.email, password=password)
            print(
                f"Password updated for administrator {admin_id} "
                f"({normalize_email(args.email)})."
            )
        else:
            admin_id = create_admin(
                conn, name=args.name, email=args.email, password=password
            )
            print(
                f"Administrator created: {admin_id} ({normalize_email(args.email)})."
            )
        return 0
    except (RecoveryError, HTTPException) as exc:
        detail = exc.detail if isinstance(exc, HTTPException) else str(exc)
        print(f"Recovery failed: {detail}", file=sys.stderr)
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
