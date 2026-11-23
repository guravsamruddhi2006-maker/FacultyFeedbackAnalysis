-- Faculty self-selection and subject requests.
--
-- This migration is additive and idempotent. It never drops or truncates a
-- table, column or row. It deliberately does NOT create selections for existing
-- course offerings: faculty must choose their own subjects. See migration 003
-- for the correction of databases where an earlier revision backfilled them.
BEGIN;

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

COMMIT;
