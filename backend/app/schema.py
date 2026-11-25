"""Idempotent runtime schema upgrade and data correction.

Production database credentials are managed by the hosting platform, so the
additive migrations in ``database/migrations`` are also applied here on the
first database-backed request of each process.

Guarantees:

* only creates missing tables, columns and indexes,
* never drops or truncates a table, column or row,
* never assigns subjects to faculty automatically,
* deactivates the rows that the earlier migration backfilled from existing
  course offerings, while keeping those offerings and their feedback intact,
* adds the reversible student archive flag without changing existing accounts,
* records applied corrections in ``schema_migrations`` so each correction runs
  at most once,
* takes a transaction-scoped advisory lock so concurrent cold starts cannot
  race each other.
"""

from __future__ import annotations

import logging

import psycopg

from app.db import connect


logger = logging.getLogger("facultyinsight.schema")

_schema_ready = False

_REQUIRED_TABLES = ("faculty_subject_selections", "subject_requests")

_BACKFILL_CORRECTION = "003_deactivate_backfilled_selections"

_STUDENT_ACTIVE_SUPPORT = "004_student_archive_support"

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS faculty_subject_selections (
    selection_id    SERIAL PRIMARY KEY,
    faculty_id      INTEGER NOT NULL REFERENCES faculty(faculty_id) ON UPDATE CASCADE ON DELETE CASCADE,
    subject_code    VARCHAR(20) NOT NULL REFERENCES subjects(subject_code) ON UPDATE CASCADE ON DELETE RESTRICT,
    academic_year   VARCHAR(9) NOT NULL REFERENCES academic_years(academic_year) ON UPDATE CASCADE ON DELETE RESTRICT,
    semester_number INTEGER NOT NULL REFERENCES semesters(semester_number) ON UPDATE CASCADE ON DELETE RESTRICT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    origin          VARCHAR(20) NOT NULL DEFAULT 'faculty',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ,
    CONSTRAINT faculty_subject_selections_unique UNIQUE (faculty_id, subject_code, academic_year, semester_number)
);

CREATE TABLE IF NOT EXISTS subject_requests (
    request_id      SERIAL PRIMARY KEY,
    faculty_id      INTEGER NOT NULL REFERENCES faculty(faculty_id) ON UPDATE CASCADE ON DELETE CASCADE,
    subject_code    VARCHAR(20) NOT NULL,
    subject_name    VARCHAR(180) NOT NULL,
    semester_number INTEGER NOT NULL REFERENCES semesters(semester_number) ON UPDATE CASCADE ON DELETE RESTRICT,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    admin_note      VARCHAR(500),
    reviewed_by     INTEGER REFERENCES admins(admin_id) ON UPDATE CASCADE ON DELETE SET NULL,
    reviewed_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT subject_requests_status_check CHECK (status IN ('pending', 'approved', 'rejected')),
    CONSTRAINT subject_requests_code_format_check CHECK (length(trim(subject_code)) >= 2),
    CONSTRAINT subject_requests_name_check CHECK (length(trim(subject_name)) >= 3)
);

CREATE TABLE IF NOT EXISTS schema_migrations (
    version     VARCHAR(80) PRIMARY KEY,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_faculty_selections_faculty
    ON faculty_subject_selections(faculty_id, is_active);
CREATE INDEX IF NOT EXISTS idx_faculty_selections_scope
    ON faculty_subject_selections(academic_year, semester_number, subject_code, is_active);
CREATE UNIQUE INDEX IF NOT EXISTS idx_subject_requests_pending_code
    ON subject_requests(subject_code) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_subject_requests_faculty
    ON subject_requests(faculty_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_subject_requests_status
    ON subject_requests(status, created_at DESC);
"""

# The earlier migration inserted one selection per existing course offering.
# Those rows share the migration transaction timestamp, were never edited by a
# faculty member (updated_at IS NULL) and point at an offering created before
# the selection. An explicit faculty selection creates or reuses its offering in
# the same transaction, so its timestamps match. This identifies the automatic
# backfill without touching any genuine selection.
_CORRECTION_SQL = f"""
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     VARCHAR(80) PRIMARY KEY,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE faculty_subject_selections
    ADD COLUMN IF NOT EXISTS origin VARCHAR(20) NOT NULL DEFAULT 'faculty';

-- Reference data the dropdowns must always offer, even with no offerings.
INSERT INTO academic_years (academic_year)
VALUES ('2026-27'), ('2027-28')
ON CONFLICT (academic_year) DO NOTHING;

INSERT INTO semesters (semester_number)
VALUES (1), (2), (3), (4), (5), (6), (7), (8)
ON CONFLICT (semester_number) DO NOTHING;

UPDATE faculty_subject_selections fss
SET origin = 'backfill',
    is_active = FALSE,
    updated_at = CURRENT_TIMESTAMP
WHERE fss.origin = 'faculty'
  AND fss.is_active = TRUE
  AND fss.updated_at IS NULL
  AND fss.created_at = (SELECT MIN(created_at) FROM faculty_subject_selections)
  AND EXISTS (
      SELECT 1
      FROM course_offerings co
      WHERE co.faculty_id = fss.faculty_id
        AND co.subject_code = fss.subject_code
        AND co.academic_year = fss.academic_year
        AND co.semester_number = fss.semester_number
        AND co.created_at < fss.created_at
  );

INSERT INTO schema_migrations (version)
VALUES ('{_BACKFILL_CORRECTION}')
ON CONFLICT (version) DO NOTHING;
"""

# Reversible archive support for student accounts. The flag is additive and
# defaults to TRUE, so existing students keep working until an administrator
# explicitly archives them.
_STUDENT_ACTIVE_SQL = f"""
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     VARCHAR(80) PRIMARY KEY,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE students
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;

CREATE INDEX IF NOT EXISTS idx_students_active ON students(is_active);

INSERT INTO schema_migrations (version)
VALUES ('{_STUDENT_ACTIVE_SUPPORT}')
ON CONFLICT (version) DO NOTHING;
"""


def _tables_present(conn: psycopg.Connection) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT to_regclass(%s) AS selections, to_regclass(%s) AS requests",
            (f"public.{_REQUIRED_TABLES[0]}", f"public.{_REQUIRED_TABLES[1]}"),
        )
        row = cur.fetchone()
    return bool(row and row["selections"] and row["requests"])


def _migration_applied(conn: psycopg.Connection, version: str) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT to_regclass('public.schema_migrations') AS table")
        if cur.fetchone()["table"] is None:
            return False
        cur.execute("SELECT 1 FROM schema_migrations WHERE version = %s", (version,))
        return cur.fetchone() is not None


def _correction_applied(conn: psycopg.Connection) -> bool:
    return _migration_applied(conn, _BACKFILL_CORRECTION)


def ensure_runtime_schema() -> None:
    """Create missing objects and apply the one-time backfill correction.

    Failures are logged and swallowed: preview deployments without a database
    must keep working, and the API already reports a 503 for real outages. The
    next request retries because the ready flag is only set on success.
    """

    global _schema_ready
    if _schema_ready:
        return
    try:
        conn = connect()
    except psycopg.OperationalError:
        logger.warning("Skipping schema check: database is unavailable.")
        return
    try:
        if not _tables_present(conn):
            conn.rollback()
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute("SELECT pg_advisory_xact_lock(hashtext('facultyinsight_schema_002'))")
                    cur.execute(_SCHEMA_SQL)
            conn.commit()
            logger.info("Created the faculty self-selection tables.")

        if not _correction_applied(conn):
            conn.rollback()
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute("SELECT pg_advisory_xact_lock(hashtext('facultyinsight_schema_003'))")
                    cur.execute(_CORRECTION_SQL)
            conn.commit()
            logger.info("Deactivated automatically backfilled faculty selections.")

        if not _migration_applied(conn, _STUDENT_ACTIVE_SUPPORT):
            conn.rollback()
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute("SELECT pg_advisory_xact_lock(hashtext('facultyinsight_schema_004'))")
                    cur.execute(_STUDENT_ACTIVE_SQL)
            conn.commit()
            logger.info("Added the reversible student archive flag.")

        _schema_ready = True
    except psycopg.Error:
        logger.exception("Could not apply the faculty self-selection schema upgrade.")
    finally:
        conn.close()
