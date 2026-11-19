-- Additive upgrade for the legacy Faculty Feedback database.
-- This migration never drops a table, column or row.
BEGIN;

ALTER TABLE faculty ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ;
UPDATE faculty SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;
ALTER TABLE faculty ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE faculty ALTER COLUMN created_at SET NOT NULL;

ALTER TABLE students ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ;
UPDATE students SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;
ALTER TABLE students ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE students ALTER COLUMN created_at SET NOT NULL;

ALTER TABLE admins ADD COLUMN IF NOT EXISTS is_active BOOLEAN;
UPDATE admins SET is_active = TRUE WHERE is_active IS NULL;
ALTER TABLE admins ALTER COLUMN is_active SET DEFAULT TRUE;
ALTER TABLE admins ALTER COLUMN is_active SET NOT NULL;

ALTER TABLE admins ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ;
UPDATE admins SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;
ALTER TABLE admins ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE admins ALTER COLUMN created_at SET NOT NULL;

ALTER TABLE course_offerings ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ;
UPDATE course_offerings SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;
ALTER TABLE course_offerings ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE course_offerings ALTER COLUMN created_at SET NOT NULL;

ALTER TABLE feedback ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ;

-- The legacy table has no default on submitted_at, so inserts from the
-- application failed with a NOT NULL violation. Give it a default that matches
-- the canonical schema; existing rows are untouched.
UPDATE feedback SET submitted_at = CURRENT_TIMESTAMP WHERE submitted_at IS NULL;
ALTER TABLE feedback ALTER COLUMN submitted_at SET DEFAULT CURRENT_TIMESTAMP;

-- Legacy comments are present and valid. Guard the NOT NULL migration anyway.
UPDATE feedback
SET comment = 'Legacy feedback comment was not supplied.'
WHERE comment IS NULL OR length(trim(comment)) < 10;
ALTER TABLE feedback ALTER COLUMN comment SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'semesters_number_check') THEN
        ALTER TABLE semesters ADD CONSTRAINT semesters_number_check CHECK (semester_number BETWEEN 1 AND 8);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'academic_years_format_check') THEN
        ALTER TABLE academic_years ADD CONSTRAINT academic_years_format_check CHECK (academic_year ~ '^[0-9]{4}-[0-9]{2}$');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'faculty_status_check') THEN
        ALTER TABLE faculty ADD CONSTRAINT faculty_status_check CHECK (status IN ('pending', 'approved', 'rejected', 'inactive'));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'students_usn_check') THEN
        ALTER TABLE students ADD CONSTRAINT students_usn_check CHECK (student_id ~ '^[A-Za-z0-9]{6,50}$');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'feedback_comment_length_check') THEN
        ALTER TABLE feedback ADD CONSTRAINT feedback_comment_length_check CHECK (char_length(comment) BETWEEN 10 AND 1000);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'feedback_answer_unique_question') THEN
        ALTER TABLE feedback_answer ADD CONSTRAINT feedback_answer_unique_question UNIQUE (feedback_id, question_id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'feedback_questions_text_check') THEN
        ALTER TABLE feedback_questions ADD CONSTRAINT feedback_questions_text_check CHECK (length(trim(question_text)) >= 5);
    END IF;
END $$;

-- Validate legacy constraints that were created as NOT VALID.
ALTER TABLE feedback_periods VALIDATE CONSTRAINT feedback_period_dates_check;
ALTER TABLE faculty VALIDATE CONSTRAINT faculty_department_fk;
ALTER TABLE students VALIDATE CONSTRAINT students_department_fk;
ALTER TABLE subjects VALIDATE CONSTRAINT subjects_semester_fk;
ALTER TABLE feedback_periods VALIDATE CONSTRAINT feedback_periods_academic_year_fk;
ALTER TABLE feedback_periods VALIDATE CONSTRAINT feedback_periods_semester_fk;
ALTER TABLE feedback_answer VALIDATE CONSTRAINT feedback_answer_fk;
ALTER TABLE feedback_answer VALIDATE CONSTRAINT feedbacj_answer_question_fk;

CREATE TABLE IF NOT EXISTS audit_logs (
    log_id          BIGSERIAL PRIMARY KEY,
    actor_role      VARCHAR(20) NOT NULL,
    actor_id        VARCHAR(50) NOT NULL,
    action          VARCHAR(80) NOT NULL,
    entity_type     VARCHAR(80),
    entity_id       VARCHAR(80),
    details         JSONB NOT NULL DEFAULT '{}'::jsonb,
    ip_address      VARCHAR(64),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_faculty_status ON faculty(status);
CREATE INDEX IF NOT EXISTS idx_course_offerings_faculty ON course_offerings(faculty_id);
CREATE INDEX IF NOT EXISTS idx_course_offerings_scope ON course_offerings(academic_year, semester_number, subject_code);
CREATE INDEX IF NOT EXISTS idx_feedback_offering ON feedback(offering_id);
CREATE INDEX IF NOT EXISTS idx_feedback_student ON feedback(student_id);
CREATE INDEX IF NOT EXISTS idx_feedback_answers_question ON feedback_answer(question_id);
CREATE INDEX IF NOT EXISTS idx_feedback_period_dates ON feedback_periods(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at DESC);

COMMIT;
