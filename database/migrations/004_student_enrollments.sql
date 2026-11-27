-- Verified class rosters for faculty completion tracking.
--
-- Feedback eligibility is never inferred from every registered student. An
-- administrator explicitly enrolls students in a subject for one academic year
-- and semester, and only those rows count toward submitted/pending totals.
--
-- This migration is additive and idempotent. It never drops or truncates a
-- table, column or row, and it creates no enrollments by itself.
BEGIN;

CREATE TABLE IF NOT EXISTS student_enrollments (
    enrollment_id   SERIAL PRIMARY KEY,
    student_id      VARCHAR(50) NOT NULL REFERENCES students(student_id) ON UPDATE CASCADE ON DELETE CASCADE,
    subject_code    VARCHAR(20) NOT NULL REFERENCES subjects(subject_code) ON UPDATE CASCADE ON DELETE RESTRICT,
    academic_year   VARCHAR(9) NOT NULL REFERENCES academic_years(academic_year) ON UPDATE CASCADE ON DELETE RESTRICT,
    semester_number INTEGER NOT NULL REFERENCES semesters(semester_number) ON UPDATE CASCADE ON DELETE RESTRICT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT student_enrollments_unique UNIQUE (student_id, subject_code, academic_year, semester_number)
);

CREATE INDEX IF NOT EXISTS idx_student_enrollments_scope
    ON student_enrollments(subject_code, academic_year, semester_number);
CREATE INDEX IF NOT EXISTS idx_student_enrollments_student
    ON student_enrollments(student_id);

CREATE TABLE IF NOT EXISTS schema_migrations (
    version     VARCHAR(80) PRIMARY KEY,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO schema_migrations (version)
VALUES ('004_student_enrollment_roster')
ON CONFLICT (version) DO NOTHING;

COMMIT;
