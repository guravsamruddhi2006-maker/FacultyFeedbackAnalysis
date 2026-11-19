# FacultyInsight AI — Testing Documentation

## Backend

Framework: pytest + FastAPI TestClient (httpx).

Location: `backend/tests/`.

- `conftest.py` — isolated database `faculty_feedback_test`, schema loaded from `database/schema.sql`, truncation between tests, fixtures for admin/faculty/students/offerings/questions, helpers for bearer tokens and feedback submission.
- `test_auth.py` — setup once, registration, login, approval flow, pending rejection, change password.
- `test_admin_catalog.py` — admin catalog CRUD, faculty approval, student management.
- `test_analytics.py` — aggregates reflect real ratings, scaffolds, admin analytics, model info, sentiment endpoint.
- `test_faculty_isolation.py` — faculty cannot see another faculty's feedback; student identifiers never returned; role boundaries; admin faculty view.
- `test_ml_insights.py` — insights endpoint, evidence-based recommendations, strengths, admin faculty insights.
- `test_reports.py` — CSV/PDF exports, access control, format validation.
- `test_student_feedback.py` — dashboard defaults, form questions, duplicate rejection, atomic edit, rating validation, closed-period behaviour, ownership.
- `test_analytics_engine.py` — reusable Pandas/Numpy analytics engine.

Run:

```bash
backend/.venv/bin/python -m pytest backend/tests
```

## Frontend

Framework: Vitest + React Testing Library + jsdom.

- `src/pages/Public.test.tsx` — landing/about render.
- `src/components/ProtectedRoute.test.tsx` — route guard behaviour.

Run:

```bash
cd frontend
npm test
npm run build   # tsc --noEmit + vite build
```

## Browser end-to-end tests (Playwright)

Framework: Playwright (`@playwright/test`) + Chromium headless.

- `playwright.config.ts` — webServer starts the Vite dev server (`npm run dev`) on `http://localhost:5173`.
- `e2e/public.spec.ts` — landing page headline, about page mission.
- `e2e/auth.spec.ts` — unauthenticated visits to `/student`, `/faculty`, `/admin` redirect to `/login`.
- `e2e/roles.spec.ts` — authenticated local demo logins reach the role dashboards (admin/faculty/student).
- `e2e/deep/admin.spec.ts` — deep admin workflows (login + department overview, faculty management lists,
  pending faculty blocked login, admin approves pending faculty).
- `e2e/deep/admin_crud.spec.ts` — deep admin catalog/period/audit workflows and faculty register+reject flow.
- `e2e/deep/faculty_insights.spec.ts` — deep faculty AI insights / question-wise performance / comparisons and
  anonymous comments.
- `e2e/deep/faculty.spec.ts` — deep faculty workflow (approved faculty reaches teaching dashboard).
- `e2e/deep/student_registration.spec.ts` — deep student workflow (registration creates account).
- `e2e/deep/student.spec.ts` — deep student workflows (login, submit full feedback, edit open-period submission).
- `e2e/deep/security_access.spec.ts` — deep security workflows (cross-role page access denied).

Run:

```bash
cd frontend
npx playwright install chromium   # one-time browser download
npm run test:e2e                    # or: npx playwright test
npx playwright test e2e/deep --workers=1   # deep workflow focused run
```

Final results (2026-11-18, Phase Next): **26 passed, 0 failed** (Chromium headless; full suite: auth guards 4, deep admin_crud 3, deep admin 4, deep faculty_insights 2, deep faculty 1, deep security 3, deep student_registration 1, deep student 3, public 2, roles 3; ~46s with `--workers=1`).

Deep workflow E2E focused results (2026-11-18, Phase Next): **17 passed, 0 failed** — admin_crud 3, admin 4, faculty_insights 2, faculty 1, security 3, student_registration 1, student 3. See `DEEP_WORKFLOW_E2E_REPORT.md` and `PHASE_NEXT_REPORT.md` for the full reports.

## Security tests

Covered: unauthorized access, role escalation boundaries, input validation, password storage (bcrypt), duplicate submissions, closed-period enforcement, faculty isolation, student identifier non-exposure.

## Notes

- Tests never run against the development database; they use `faculty_feedback_test`.
- The suite currently passes: backend **51 passed** (2026-11-19, Phase 20 run after API-docs production fix), frontend **4 passed** (unit), frontend production build **passed**, browser E2E **26 passed** (2026-11-18 full suite) and deep E2E **17 passed** (2026-11-18, Phase Next).
- Playwright e2e specs live in `frontend/e2e/` and are excluded from the Vitest unit-test run via `test.exclude` in `frontend/vite.config.ts`.
- Deep workflow browser specs live in `frontend/e2e/deep/` and target the isolated test database accounts (`admin@test.local`, `alpha@test.local`, `beta@test.local`, `pending@test.local`, student `4UB26CS001`).
