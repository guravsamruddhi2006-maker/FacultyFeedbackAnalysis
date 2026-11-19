# Phase 2 — Role-based Application Pages

**Completed:** 2026-11-10

## Summary

Completed the API-backed Student, Faculty, and Admin application pages by reusing the existing FastAPI services, authentication context, route guards, layout, shared UI components, and Recharts dependency. No database schema or development data was changed.

## Student

- Reused the existing dashboard to select academic year and semester and review assigned offerings, subject/faculty names, status, and submission time.
- Reused the existing feedback form with every active configured rating question (five in the existing seed/test data), required ratings, and a required constructive comment (10–1000 characters).
- Preserved read-only access to previous submissions after the feedback period closes. Updated the feedback-form GET behavior to permit reading an already-submitted response when closed, while preserving 403 responses for closed-period new submissions and edits.
- Added a regression assertion for the closed-period read-only flow.

## Faculty

- Added an API-backed teaching dashboard for assigned offerings, academic year/semester/subject filters, response totals, average ratings, and question-wise performance.
- Added responsive Recharts views for question averages and the faculty member's own academic-year comparison.
- Added evidence-based strengths and improvement areas, plus anonymous comments and a paginated/filterable comments screen.
- Dashboard, offering, comparison, and comment requests use existing faculty `/me` endpoints, which derive faculty scope from the JWT. Existing isolation tests verify that faculty cannot see another faculty member's feedback and that student identifiers are absent.

## Admin

- Added department-wide aggregate counts, response coverage, semester/year analytics, question averages, and faculty performance views.
- Added faculty creation and status management, including pending approval/rejection and deactivation/reactivation.
- Added student listing/creation, audited profile editing, and audited submission-metadata viewing. The details view excludes comment text and ratings.
- Added subject, course-offering, academic-year, feedback-period, and question management, using existing catalog CRUD endpoints and confirmation prompts for deletions.
- Added the admin audit-log view.
- Added `PATCH /api/admin/students/{student_id}` with admin-only authorization, input validation, and an audit record for safe name/department updates. Student deletion is not exposed because the existing schema cascades deletes to feedback records.

## Files changed

- `frontend/src/App.tsx`
- `frontend/src/pages/admin/AdminDashboard.tsx` (new)
- `frontend/src/pages/admin/AdminManagement.tsx` (new)
- `frontend/src/pages/faculty/FacultyDashboard.tsx` (new)
- `backend/app/api/students.py`
- `backend/app/api/admin.py`
- `backend/app/schemas/admin.py`
- `backend/tests/test_student_feedback.py`
- `backend/tests/test_admin_catalog.py`
- `PROJECT_PROGRESS.md`
- `PHASE2_REPORT.md` (new)

No new dashboard API was needed; existing endpoints supplied the requested data. The student profile update route is the only new endpoint.

## Verification

- Frontend: `npm run build` from `frontend/` — **passed** (`tsc --noEmit` and Vite production build).
- Backend: `backend/.venv/Scripts/python.exe -m pytest -q backend/tests` — **36 passed**.
- The test fixture was inspected before execution. Its target was `faculty_feedback_test`, not the configured development database `faculty_feedback`; the fixture reset only its dedicated test schema. The development database was not changed.
- Test output contained one upstream Starlette/httpx deprecation warning; there were no test failures.
- No npm install was needed; frontend dependencies were present.

## Remaining work

- Advanced analytics and model training remain out of scope and were not started.
- Student deletion/deactivation is intentionally unavailable: the schema has no student status field and deleting a student would cascade to feedback history. Any future account lifecycle feature should preserve historical feedback and be designed additively.
- Browser-based end-to-end workflows and live backend/frontend integration were not run in this phase.
