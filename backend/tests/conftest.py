"""Shared pytest fixtures for the FacultyInsight AI backend.

Tests run against a dedicated PostgreSQL database (``faculty_feedback_test`` by
default) so they can truncate and reseed freely without touching development or
production data. The schema is created once per session from
``database/schema.sql``.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterator

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db import get_db
from app.main import app

PROJECT_DIR = Path(__file__).resolve().parents[2]
SCHEMA_FILE = PROJECT_DIR / "database" / "schema.sql"
TEST_DB_NAME = os.getenv("TEST_DB_NAME", "faculty_feedback_test")

# Hash once: bcrypt is intentionally slow, and every fixture user shares the
# same test password.
TEST_PASSWORD = "Test@12345"
TEST_PASSWORD_HASH = hash_password(TEST_PASSWORD)

TRUNCATE_ORDER = (
    "audit_logs, feedback_answer, feedback, feedback_periods, feedback_questions, "
    "course_offerings, faculty_subject_selections, subject_requests, students, faculty, "
    "admins, subjects, academic_years, semesters, departments"
)


def _base_params() -> dict[str, Any]:
    if "conninfo" in settings.db_conninfo:
        return conninfo_to_dict(settings.db_conninfo["conninfo"])
    return dict(settings.db_conninfo)


def _test_params() -> dict[str, Any]:
    params = _base_params()
    params["dbname"] = TEST_DB_NAME
    return params


def _statements(sql: str) -> Iterator[str]:
    for chunk in sql.split(";"):
        lines = [line for line in chunk.splitlines() if not line.strip().startswith("--")]
        statement = "\n".join(lines).strip()
        if statement and statement.upper() not in {"BEGIN", "COMMIT"}:
            yield statement


@pytest.fixture(scope="session", autouse=True)
def test_database() -> Iterator[None]:
    """Create and initialise the isolated test database once per session."""
    maintenance = dict(_base_params())
    maintenance["dbname"] = "postgres"
    admin = psycopg.connect(**maintenance, autocommit=True)
    try:
        with admin.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (TEST_DB_NAME,))
            if cur.fetchone() is None:
                cur.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')
    finally:
        admin.close()

    conn = psycopg.connect(**_test_params(), autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute("DROP SCHEMA IF EXISTS public CASCADE")
            cur.execute("CREATE SCHEMA public")
            for statement in _statements(SCHEMA_FILE.read_text(encoding="utf-8")):
                cur.execute(statement)
    finally:
        conn.close()
    yield


@pytest.fixture()
def db(test_database: None) -> Iterator[psycopg.Connection]:
    """A clean, empty database connection for one test."""
    conn = psycopg.connect(**_test_params(), row_factory=dict_row)
    try:
        with conn.cursor() as cur:
            cur.execute(f"TRUNCATE {TRUNCATE_ORDER} RESTART IDENTITY CASCADE")
        conn.commit()
        yield conn
    finally:
        conn.close()


@pytest.fixture()
def data(db: psycopg.Connection) -> dict[str, Any]:
    """Seed a minimal, deterministic dataset used by the API tests."""
    with db.transaction():
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO departments (name, code) VALUES (%s, %s) RETURNING id",
                ("Computer Science and Engineering", "CSE"),
            )
            department_id = cur.fetchone()["id"]

            for number in range(1, 9):
                cur.execute("INSERT INTO semesters (semester_number) VALUES (%s)", (number,))
            cur.execute("INSERT INTO academic_years (academic_year) VALUES (%s)", ("2026-27",))
            cur.execute("INSERT INTO academic_years (academic_year) VALUES (%s)", ("2027-28",))

            subjects = {
                "CS501": ("Data Structures", 5),
                "CS502": ("Operating Systems", 5),
                "CS503": ("Database Systems", 5),
            }
            for code, (name, semester) in subjects.items():
                cur.execute(
                    "INSERT INTO subjects (subject_code, subject_name, semester_number) VALUES (%s, %s, %s)",
                    (code, name, semester),
                )

            questions = [
                "Explains concepts clearly",
                "Has good subject knowledge",
                "Encourages student participation",
                "Uses practical examples",
                "Completes the syllabus",
            ]
            question_ids = []
            for text in questions:
                cur.execute(
                    "INSERT INTO feedback_questions (question_text) VALUES (%s) RETURNING question_id",
                    (text,),
                )
                question_ids.append(cur.fetchone()["question_id"])

            faculty: dict[str, int] = {}
            for key, name, email, status in (
                ("a", "Faculty Alpha", "alpha@test.local", "approved"),
                ("b", "Faculty Beta", "beta@test.local", "approved"),
                ("pending", "Faculty Pending", "pending@test.local", "pending"),
            ):
                cur.execute(
                    """
                    INSERT INTO faculty (name, email, password_hash, department_id, status)
                    VALUES (%s, %s, %s, %s, %s) RETURNING faculty_id
                    """,
                    (name, email, TEST_PASSWORD_HASH, department_id, status),
                )
                faculty[key] = cur.fetchone()["faculty_id"]

            cur.execute(
                "INSERT INTO students (student_id, name, department_id, password_hash) VALUES (%s, %s, %s, %s)",
                ("4UB26CS001", "Test Student", department_id, TEST_PASSWORD_HASH),
            )
            cur.execute(
                "INSERT INTO students (student_id, name, department_id, password_hash) VALUES (%s, %s, %s, %s)",
                ("4UB26CS002", "Second Student", department_id, TEST_PASSWORD_HASH),
            )

            cur.execute(
                """
                INSERT INTO admins (name, email, password_hash)
                VALUES (%s, %s, %s) RETURNING admin_id
                """,
                ("Test Administrator", "admin@test.local", TEST_PASSWORD_HASH),
            )
            admin_id = cur.fetchone()["admin_id"]

            offerings: dict[str, int] = {}
            selections: dict[str, int] = {}
            for key, subject, faculty_key in (
                ("a", "CS501", "a"),
                ("b", "CS502", "b"),
                ("a2", "CS503", "a"),
            ):
                cur.execute(
                    """
                    INSERT INTO course_offerings (academic_year, semester_number, subject_code, faculty_id)
                    VALUES (%s, %s, %s, %s) RETURNING offering_id
                    """,
                    ("2026-27", 5, subject, faculty[faculty_key]),
                )
                offerings[key] = cur.fetchone()["offering_id"]
                cur.execute(
                    """
                    INSERT INTO faculty_subject_selections
                        (faculty_id, subject_code, academic_year, semester_number, is_active)
                    VALUES (%s, %s, %s, %s, TRUE) RETURNING selection_id
                    """,
                    (faculty[faculty_key], subject, "2026-27", 5),
                )
                selections[key] = cur.fetchone()["selection_id"]

            cur.execute(
                """
                INSERT INTO feedback_periods (academic_year, semester_number, start_date, end_date)
                VALUES (%s, %s, CURRENT_TIMESTAMP - INTERVAL '1 day', CURRENT_TIMESTAMP + INTERVAL '7 days')
                """,
                ("2026-27", 5),
            )
            cur.execute(
                """
                INSERT INTO feedback_periods (academic_year, semester_number, start_date, end_date)
                VALUES (%s, %s, CURRENT_TIMESTAMP - INTERVAL '30 days', CURRENT_TIMESTAMP - INTERVAL '20 days')
                """,
                ("2027-28", 5),
            )

    return {
        "department_id": department_id,
        "question_ids": question_ids,
        "faculty": faculty,
        "offerings": offerings,
        "selections": selections,
        "admin_id": admin_id,
        "student_id": "4UB26CS001",
        "second_student_id": "4UB26CS002",
    }


@pytest.fixture()
def client(db: psycopg.Connection) -> Iterator[TestClient]:
    """A TestClient whose DB dependency points at the isolated test database."""

    def override_get_db() -> Iterator[psycopg.Connection]:
        conn = psycopg.connect(**_test_params(), row_factory=dict_row)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    from app.core.deps import login_rate_limiter

    login_rate_limiter._hits.clear()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def bearer(subject: str | int, role: str) -> dict[str, str]:
    token, _ = create_access_token(subject=str(subject), role=role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_headers(data: dict[str, Any]) -> dict[str, str]:
    return bearer(data["admin_id"], "admin")


@pytest.fixture()
def faculty_a_headers(data: dict[str, Any]) -> dict[str, str]:
    return bearer(data["faculty"]["a"], "faculty")


@pytest.fixture()
def faculty_b_headers(data: dict[str, Any]) -> dict[str, str]:
    return bearer(data["faculty"]["b"], "faculty")


@pytest.fixture()
def student_headers(data: dict[str, Any]) -> dict[str, str]:
    return bearer(data["student_id"], "student")


def ratings(data: dict[str, Any], score: int) -> list[dict[str, int]]:
    return [{"question_id": qid, "rating": score} for qid in data["question_ids"]]


def submit_feedback(
    client: TestClient,
    data: dict[str, Any],
    headers: dict[str, str],
    *,
    offering_key: str = "a",
    score: int = 5,
    comment: str = "Clear explanations and well organised lectures with useful examples.",
) -> dict[str, Any]:
    response = client.post(
        "/api/students/me/feedback",
        headers=headers,
        json={
            "offering_id": data["offerings"][offering_key],
            "ratings": ratings(data, score),
            "comment": comment,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()
