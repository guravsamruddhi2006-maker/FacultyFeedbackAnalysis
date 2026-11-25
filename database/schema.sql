-- FacultyInsight AI - canonical PostgreSQL 18 schema
-- Safe to use as a Docker init script against an empty database.
BEGIN;

CREATE TABLE IF NOT EXISTS departments (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(120) NOT NULL UNIQUE,
    code            VARCHAR(10)  NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS semesters (
    semester_number INTEGER PRIMARY KEY,
    CONSTRAINT semesters_number_check CHECK (semester_number BETWEEN 1 AND 8)
);

CREATE TABLE IF NOT EXISTS academic_years (
    academic_year VARCHAR(9) PRIMARY KEY,
    CONSTRAINT academic_years_format_check CHECK (academic_year ~ '^[0-9]{4}-[0-9]{2}$')
);

CREATE TABLE IF NOT EXISTS subjects (
    subject_code    VARCHAR(20) PRIMARY KEY,
    subject_name    VARCHAR(180) NOT NULL,
    semester_number INTEGER NOT NULL REFERENCES semesters(semester_number) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS faculty (
    faculty_id      SERIAL PRIMARY KEY,
    name            VARCHAR(120) NOT NULL,
    email           VARCHAR(160) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    department_id   INTEGER NOT NULL REFERENCES departments(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT faculty_status_check CHECK (status IN ('pending', 'approved', 'rejected', 'inactive'))
);

CREATE TABLE IF NOT EXISTS students (
    student_id      VARCHAR(50) PRIMARY KEY,
    name            VARCHAR(120) NOT NULL,
    department_id   INTEGER NOT NULL REFERENCES departments(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    password_hash   VARCHAR(255) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT students_usn_check CHECK (student_id ~ '^[A-Za-z0-9]{6,50}$')
);

CREATE TABLE IF NOT EXISTS admins (
    admin_id        SERIAL PRIMARY KEY,
    name            VARCHAR(120) NOT NULL,
    email           VARCHAR(160) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS course_offerings (
    offering_id     SERIAL PRIMARY KEY,
    academic_year   VARCHAR(9) NOT NULL REFERENCES academic_years(academic_year) ON UPDATE CASCADE ON DELETE RESTRICT,
    semester_number INTEGER NOT NULL REFERENCES semesters(semester_number) ON UPDATE CASCADE ON DELETE RESTRICT,
    subject_code    VARCHAR(20) NOT NULL REFERENCES subjects(subject_code) ON UPDATE CASCADE ON DELETE RESTRICT,
    faculty_id      INTEGER NOT NULL REFERENCES faculty(faculty_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT course_offerings_unique_assignment UNIQUE (academic_year, semester_number, subject_code, faculty_id)
);

-- Faculty choose their own teaching subjects. An administrator never assigns a
-- faculty member here, and the catalog stays independent of this relationship.
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

-- Faculty may request a subject that is missing from the official catalog.
-- A request only becomes a catalog subject after administrator approval.
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

CREATE TABLE IF NOT EXISTS feedback_questions (
    question_id     SERIAL PRIMARY KEY,
    question_text   VARCHAR(500) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT feedback_questions_text_check CHECK (length(trim(question_text)) >= 5)
);

CREATE TABLE IF NOT EXISTS feedback_periods (
    academic_year   VARCHAR(9) NOT NULL REFERENCES academic_years(academic_year) ON UPDATE CASCADE ON DELETE CASCADE,
    semester_number INTEGER NOT NULL REFERENCES semesters(semester_number) ON UPDATE CASCADE ON DELETE RESTRICT,
    start_date      TIMESTAMPTZ NOT NULL,
    end_date        TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (academic_year, semester_number),
    CONSTRAINT feedback_period_dates_check CHECK (end_date > start_date)
);

CREATE TABLE IF NOT EXISTS feedback (
    feedback_id     SERIAL PRIMARY KEY,
    student_id      VARCHAR(50) NOT NULL REFERENCES students(student_id) ON UPDATE CASCADE ON DELETE CASCADE,
    offering_id     INTEGER NOT NULL REFERENCES course_offerings(offering_id) ON UPDATE CASCADE ON DELETE CASCADE,
    submitted_at    TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ,
    comment         TEXT NOT NULL,
    CONSTRAINT feedback_comment_length_check CHECK (char_length(comment) BETWEEN 10 AND 1000),
    CONSTRAINT feedback_student_offering_unique UNIQUE (student_id, offering_id)
);

CREATE TABLE IF NOT EXISTS feedback_answer (
    answer_id       SERIAL PRIMARY KEY,
    feedback_id     INTEGER NOT NULL REFERENCES feedback(feedback_id) ON UPDATE CASCADE ON DELETE CASCADE,
    question_id     INTEGER NOT NULL REFERENCES feedback_questions(question_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    rating          INTEGER NOT NULL,
    CONSTRAINT rating_range_check CHECK (rating BETWEEN 1 AND 5),
    CONSTRAINT feedback_answer_unique_question UNIQUE (feedback_id, question_id)
);

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
CREATE INDEX IF NOT EXISTS idx_students_active ON students(is_active);
CREATE INDEX IF NOT EXISTS idx_course_offerings_faculty ON course_offerings(faculty_id);
CREATE INDEX IF NOT EXISTS idx_course_offerings_scope ON course_offerings(academic_year, semester_number, subject_code);
CREATE INDEX IF NOT EXISTS idx_faculty_selections_faculty ON faculty_subject_selections(faculty_id, is_active);
CREATE INDEX IF NOT EXISTS idx_faculty_selections_scope ON faculty_subject_selections(academic_year, semester_number, subject_code, is_active);
CREATE UNIQUE INDEX IF NOT EXISTS idx_subject_requests_pending_code
    ON subject_requests(subject_code) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_subject_requests_faculty ON subject_requests(faculty_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_subject_requests_status ON subject_requests(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_offering ON feedback(offering_id);
CREATE INDEX IF NOT EXISTS idx_feedback_student ON feedback(student_id);
CREATE INDEX IF NOT EXISTS idx_feedback_answers_question ON feedback_answer(question_id);
CREATE INDEX IF NOT EXISTS idx_feedback_period_dates ON feedback_periods(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at DESC);

COMMIT;
