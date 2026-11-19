# FacultyInsight AI — Database Documentation

Database name: **`faculty_feedback`** (PostgreSQL 18)

## 1. Overview

Normalized relational schema with master data plus transactional feedback records and an audit trail.

## 2. Tables

| Table | Purpose | Key columns |
| --- | --- | --- |
| `departments` | Department master data | `id`, `name` (UNIQUE), `code` (UNIQUE) |
| `academic_years` | Academic years | `academic_year` (PK, `YYYY-YY`) |
| `semesters` | Semesters 1–8 | `semester_number` (PK, CHECK 1..8) |
| `subjects` | Reusable subject catalogue | `subject_code` (PK), `subject_name`, `semester_number` FK |
| `faculty` | Faculty accounts | `faculty_id`, `name`, `email` (UNIQUE), `password_hash`, `department_id` FK, `status` CHECK (pending/approved/rejected/inactive) |
| `students` | Student accounts | `student_id` (USN PK, CHECK alnum 6..50), `name`, `department_id` FK, `password_hash` |
| `admins` | Administrator accounts | `admin_id`, `name`, `email` (UNIQUE), `password_hash`, `is_active` |
| `course_offerings` | Subject → faculty assignment | `offering_id`, `academic_year`, `semester_number`, `subject_code`, `faculty_id`, UNIQUE (academic_year, semester_number, subject_code, faculty_id) |
| `feedback_periods` | Open/closed windows | PK (academic_year, semester_number), start/end dates CHECK end > start |
| `feedback_questions` | Configurable questions | `question_id`, `question_text` (min 5 chars), `is_active` |
| `feedback` | One submission per student per offering | `feedback_id`, `student_id` FK, `offering_id` FK, `submitted_at`, `updated_at`, `comment` (10..1000 chars) |
| `feedback_answer` | Rating rows | `answer_id`, `feedback_id`, `question_id`, `rating` CHECK 1..5, UNIQUE (feedback_id, question_id) |
| `audit_logs` | Administrative audit trail | `log_id`, `actor_role`, `actor_id`, `action`, `entity_type`, `entity_id`, `details` JSONB, `ip_address`, `created_at` |

## 3. Relationships

- Faculty → Department (many-to-one).
- Student → Department (many-to-one).
- Subject → Semester (many-to-one).
- Course offering → Subject, Faculty, Academic year, Semester.
- Feedback → Student, Course offering (one-to-many via answers).
- Feedback answer → Feedback, Question.

## 4. Integrity rules

- One feedback per student per offering: `UNIQUE (student_id, offering_id)` on `feedback`.
- One answer per question per feedback: `UNIQUE (feedback_id, question_id)` on `feedback_answer`.
- Period open state: `CURRENT_TIMESTAMP BETWEEN start_date AND end_date`.
- Offering uniqueness per (year, semester, subject, faculty).

## 5. Migrations and backups

- Canonical schema: `database/schema.sql` (idempotent `CREATE TABLE IF NOT EXISTS`).
- Additive upgrade for an existing legacy database: `database/migrations/001_additive_upgrade.sql` (no DROP/TRUNCATE; only ADD COLUMN IF NOT EXISTS + constraints).
- Legacy snapshot: `database/existing_schema_backup.sql`.
- Pre-upgrade backup: `database/backups/faculty_feedback_pre_upgrade.sql`.
- Base seed: `database/seed.sql` (departments, semesters, academic years, questions, subjects; Semester 8 intentionally excluded).

## 6. Semester 8 policy

Semester 8 is internship-only. No subjects or course offerings are seeded for Semester 8.

## 7. Indexes

- `idx_feedback_offering`, `idx_feedback_student`, `idx_feedback_answers_question`, `idx_feedback_period_dates`, `idx_course_offerings_*`, `idx_faculty_status`, `idx_audit_logs_created`.

## 8. Safety rules followed during development

- No destructive migrations against the live database.
- Test database `faculty_feedback_test` is used by the backend test suite.
- No student identities are exposed through faculty/admin analytics or exports.
