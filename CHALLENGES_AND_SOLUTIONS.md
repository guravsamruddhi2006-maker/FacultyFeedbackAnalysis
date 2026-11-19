# FacultyInsight AI — Challenges and Solutions

## 1. Empty/incorrect frontend app module

**Challenge:** `frontend/src/main.tsx` imported `./App` while the only matching file was an empty `src/app.tsx`.

**Solution:** Canonical `src/App.tsx` created; import and module casing aligned; production build passes.

## 2. Legacy database compatibility

**Challenge:** Existing legacy schema missing defaults/constraints/migration columns.

**Solution:** Additive migration only (`001_additive_upgrade.sql`), no destructive statements; backup snapshots preserved.

## 3. Subject identity

**Challenge:** Requirement of subject-code primary key reused across academic years.

**Solution:** `subjects.subject_code` is PK; offerings bind year/semester/subject/faculty.

## 4. Semester 8

**Challenge:** Semester 8 must be internship-only.

**Solution:** Semesters 1–8 seeded; no Semester 8 subjects/offers intentionally.

## 5. One submission per student per offering

**Challenge:** Prevent duplicates while allowing edits during open periods.

**Solution:** DB unique constraint + transactional flow + period checks + ownership checks.

## 6. Faculty isolation vs. admin analytics

**Challenge:** Admin may need faculty analytics while faculty must not see other faculty.

**Solution:** Faculty endpoints scope by JWT; admin endpoints use explicit faculty IDs with admin role.

## 7. Sentiment honesty

**Challenge:** Avoid presenting heuristic lexicon scores as trained ML confidence.

**Solution:** Confidence documented; trained model gated on validated metadata; demo training set produced unvalidated model.

## 8. Feedback period transitions

**Challenge:** Closed periods must block writes but allow read-only history.

**Solution:** Period open flag computed from dates; writes check it; reads allowed.

## 9. Test database safety

**Challenge:** Destructive tests against dev DB unacceptable.

**Solution:** Dedicated `faculty_feedback_test` database with schema reload and truncation fixtures.

## 10. Frontend/backend contract drift

**Challenge:** Dashboard payload shapes evolve.

**Solution:** TypeScript types shared in `frontend/src/lib/types.ts`; API error handling surfaced via toasts/alerts.
