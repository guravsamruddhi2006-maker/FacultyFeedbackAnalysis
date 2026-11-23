-- Correct the automatic faculty-subject assignments created by migration 002.
--
-- Migration 002 copied every existing course offering into
-- faculty_subject_selections. Those rows were never chosen by a faculty member,
-- so they must not remain active. This migration is additive and idempotent:
-- it never deletes a row, offering, feedback record or audit entry.
--
-- Identification of the automatic rows:
--   * they share the earliest selection timestamp (the backfill transaction),
--   * they were never edited by a faculty member (updated_at IS NULL),
--   * their course offering existed before the selection was inserted.
-- An explicit faculty selection creates or reuses its offering in the same
-- transaction, so its timestamps match and it is left untouched.
BEGIN;

ALTER TABLE faculty_subject_selections
    ADD COLUMN IF NOT EXISTS origin VARCHAR(20) NOT NULL DEFAULT 'faculty';

CREATE TABLE IF NOT EXISTS schema_migrations (
    version     VARCHAR(80) PRIMARY KEY,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Reference data that the dropdowns must always offer, even without offerings.
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
VALUES ('003_deactivate_backfilled_selections')
ON CONFLICT (version) DO NOTHING;

COMMIT;
