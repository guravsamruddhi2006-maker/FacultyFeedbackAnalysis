"""Create an administrator account from the command line.

Usage:
    python -m app.scripts.create_admin --name "Dept Admin" --email admin@example.edu
"""

from __future__ import annotations

import argparse
import getpass

from psycopg.errors import UniqueViolation

from app.core.security import hash_password, normalize_email
from app.db import db_transaction


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a FacultyInsight AI administrator.")
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", help="Password (prompted securely when omitted)")
    args = parser.parse_args()
    password = args.password or getpass.getpass("Password: ")
    try:
        with db_transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO admins (name, email, password_hash) VALUES (%s, %s, %s) RETURNING admin_id",
                    (args.name.strip(), normalize_email(args.email), hash_password(password)),
                )
                admin_id = cur.fetchone()["admin_id"]
        print(f"Created admin {admin_id} ({normalize_email(args.email)}).")
    except UniqueViolation:
        raise SystemExit("An admin with that email already exists.")


if __name__ == "__main__":
    main()
