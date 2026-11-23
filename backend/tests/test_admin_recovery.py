"""Operator-only administrator recovery helpers."""

from __future__ import annotations

import psycopg
import pytest
from fastapi import HTTPException

from app.core.security import verify_password
from app.recover_admin import (
    RecoveryError,
    create_admin,
    list_admins,
    reset_admin_password,
)


def test_recovery_lists_existing_admins(db: psycopg.Connection, data: dict) -> None:
    rows = list_admins(db)
    assert any(row["admin_id"] == data["admin_id"] for row in rows)
    assert all("password_hash" not in row for row in rows)


def test_recovery_creates_normalised_admin(db: psycopg.Connection, data: dict) -> None:
    admin_id = create_admin(
        db,
        name="Recovered Admin",
        email="  Recovered@College.EDU ",
        password="Recovery1Pass",
    )

    with db.cursor() as cur:
        cur.execute(
            "SELECT name, email, password_hash FROM admins WHERE admin_id = %s",
            (admin_id,),
        )
        row = cur.fetchone()
    assert row["name"] == "Recovered Admin"
    assert row["email"] == "recovered@college.edu"
    assert row["password_hash"] != "Recovery1Pass"
    assert verify_password("Recovery1Pass", row["password_hash"])


def test_recovery_refuses_duplicate_email(db: psycopg.Connection, data: dict) -> None:
    with pytest.raises(RecoveryError, match="already exists"):
        create_admin(
            db,
            name="Duplicate",
            email="ADMIN@TEST.LOCAL",
            password="Recovery1Pass",
        )


def test_recovery_reset_requires_existing_admin(db: psycopg.Connection, data: dict) -> None:
    with pytest.raises(RecoveryError, match="No administrator"):
        reset_admin_password(
            db,
            email="missing@test.local",
            password="Recovery1Pass",
        )


def test_recovery_reset_updates_only_the_requested_admin(
    db: psycopg.Connection, data: dict
) -> None:
    admin_id = reset_admin_password(
        db,
        email="ADMIN@TEST.LOCAL",
        password="BrandNewAdmin1Pass",
    )
    assert admin_id == data["admin_id"]

    with db.cursor() as cur:
        cur.execute("SELECT password_hash FROM admins WHERE admin_id = %s", (admin_id,))
        assert verify_password("BrandNewAdmin1Pass", cur.fetchone()["password_hash"])


def test_recovery_rejects_weak_passwords(db: psycopg.Connection, data: dict) -> None:
    with pytest.raises(HTTPException):
        create_admin(
            db,
            name="Weak Password",
            email="weak-admin@test.local",
            password="short",
        )
