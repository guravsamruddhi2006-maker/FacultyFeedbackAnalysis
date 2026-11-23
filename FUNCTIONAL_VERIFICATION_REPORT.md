# Functional Verification Report — FacultyInsight AI

Date: 2026-11-21
Production URL: https://faculty-feedback-system-blush.vercel.app
Production deployment: `dpl_5w8jTUxRqCfJwEgzVbWa6wWFN8YW` (READY, aliased)

## 1. Outcome

The application is a working college feedback system with no marketing or
promotional content. The site opens directly on the sign-in page, all three
roles can sign in against the real Neon PostgreSQL database, faculty
registration correctly explains existing and pending accounts, and the
one-time administrator setup no longer shows a misleading active form.

No redesign was performed. Branding, colours, typography, forms, buttons,
spacing, routes and responsive behaviour were preserved.

## 2. Marketing content removed

| Removed | Where |
| --- | --- |
| "Turning student feedback into better teaching." | Auth split-screen panel, page metadata, backend root metadata |
| "Anonymous, validated feedback with strict faculty isolation..." | Auth split-screen panel |
| Promotional bullets about anonymity, faculty isolation and explainable sentiment | Auth split-screen panel |
| "FacultyInsight AI · Academic feedback platform" | Auth page footer |
| "Better teaching, together" | Brand sub-label |
| Marketing landing page and About page | `frontend/src/pages/Public.tsx` deleted; `/` redirects to `/login` (or the role dashboard when signed in); `/about` returns the 404 page |

The authentication pages are now a single clean sign-in / registration card
with the existing FacultyInsight AI logo and the Student, Faculty and
Administrator tabs. No promotional text replaced the removed content.

## 3. Defects fixed in this pass

| Defect | Fix |
| --- | --- |
| Completed first-admin setup still displayed an active form | Added public `GET /api/auth/setup-status`; `/setup` now shows a "Setup already completed" state with a sign-in button and never renders the form after setup |
| First-admin link shown after setup | Login page hides "Create the first admin" when setup is complete |
| Faculty registration reported a vague "already exists" error | Registration now pre-checks the email and returns a status-specific 409: pending (explains approval), approved (directs to sign in) or inactive (contact administrator); no duplicate row is inserted |
| No path forward from a duplicate email | Registration error includes a link to the correct sign-in tab and preselects that tab |
| Student login could not distinguish a missing account from a wrong password | Login verifies USN format, normalizes case, looks up the record and runs bcrypt; missing account and incorrect password now return distinct 401 messages |
| Faculty login showed "database is temporarily unavailable" | Investigated production: `/health` and `/health/db` were 200, admin/faculty/student logins succeeded and no 5xx or error logs existed in the retention window. The 503 was a transient managed-Postgres cold start, so connections now use a bounded connect timeout and a short retry/backoff; genuine failures still surface as an honest 503 |
| Faculty login errors were generic | Missing account, incorrect password, pending approval and inactive account now return distinct, honest messages |
| Setup 403 message told users to ask an existing admin | Now directs them to sign in with their administrator account |

## 4. Verification results

### Automated tests

| Suite | Command | Result |
| --- | --- | --- |
| Backend pytest | `python -m pytest -q` | **54 passed** |
| Frontend Vitest | `npm test` | **6 passed (2 files)** |
| Frontend production build | `npm run build` | **passed** |

New regression coverage: setup status before/after setup, second-setup 403,
duplicate faculty registration (pending and approved), distinct student and
faculty login errors, and auth-page rendering with no marketing copy.

### Local end-to-end browser verification

11 checks passed against a local server backed by PostgreSQL: home redirect,
no marketing copy, three login tabs, hidden first-admin link, completed setup
state, student registration and login, duplicate-faculty sign-in link, pending
faculty approval message, administrator login, and mobile layout without
overflow.

### Production API verification

- `/health` → 200
- `/health/db` → 200 (`database: connected`)
- `GET /api/auth/setup-status` → `{"completed": true}`
- `POST /api/auth/admin/setup` → 403 with a sign-in instruction
- Administrator login → 200
- Faculty listing → 5 accounts (3 approved, 2 pending, no duplicates)
- Student listing → the 3 demo students persisted
- Duplicate pending faculty registration → 409 explaining approval is required
- Approved faculty login → 200; faculty dashboard → 200
- Unknown faculty → 401 "No faculty account..."; wrong password → 401 "Incorrect password..."
- Student login with lowercase USN → 200; student dashboard → 200
- Unknown USN → 401 "No student account..."; wrong password → 401 "Incorrect password..."
- Duplicate student registration → 409 without a write

### Production browser verification

12 checks passed against https://faculty-feedback-system-blush.vercel.app:

- Home redirects to `/login`
- No marketing copy on the sign-in page
- Student, Faculty and Administrator tabs render
- First-admin link is hidden after setup
- `/setup` shows the completed state and a working sign-in button
- `/about` renders the 404 page
- Duplicate pending faculty email explains approval and links to faculty sign-in
- Student login reaches the student dashboard
- Faculty login reaches the teaching overview
- Administrator login reaches the department overview
- Mobile sign-in and setup pages render at 375×812 without horizontal overflow

The pending-account 403 message was verified by automated tests and locally;
production holds two real pending accounts whose passwords are unknown, so
their login was not attempted beyond confirming that a wrong password is
rejected honestly.

## 5. Production data state

| Entity | Count |
| --- | --- |
| Departments | 1 (CSE) |
| Semesters | 8 |
| Academic years | 4 |
| Subjects | 54 |
| Faculty | 3 approved + 2 pending |
| Students | 3 |
| Course offerings | 3 |
| Open feedback periods | 1 |
| Feedback submissions | 9 |
| Administrators | 2 active |

No production records were created, deleted or modified during this pass. The
two pending faculty accounts (`guravsamruddhi7259@gmail.com`,
`faculty@gmail.com`) were left pending; an administrator must approve them
before they can sign in.

## 6. Demo accounts (synthetic, demo-only)

- Administrator: `phase4-e2e-admin@facultyinsight.local`
- Second administrator: `demo.admin@facultyinsight.local`
- Faculty: `demo.faculty.ravi@facultyinsight.local`,
  `demo.faculty.priya@facultyinsight.local`,
  `demo.faculty.kumar@facultyinsight.local`
- Students: `4UB26CS901`, `4UB26CS902`, `4UB26CS903`

These accounts exist only to demonstrate the workflows. They are not real
institutional users.

## 7. Environment and deployment notes

- Production `DATABASE_URL` and `JWT_SECRET_KEY` are stored as Vercel
  environment variables.
- `.vercelignore` excludes `.env`, virtual environments, `node_modules` and
  caches from deployment uploads.
- Preview deployments do not currently have a `DATABASE_URL` binding, so
  database-backed pages on preview return the documented
  "database temporarily unavailable" response. Preview SPA routing and static
  assets were verified; production was verified end to end.
- The SPA is served by FastAPI with `app.frontend(...)`; browser navigation to
  deep links such as `/login`, `/setup` and `/admin` returns `index.html`.
- Managed-Postgres cold starts are handled with a connect timeout and two
  retries. If the database is genuinely unreachable, the API returns 503 rather
  than a fake success.

## 8. Known limitations (stated honestly)

- Sentiment analysis is a transparent lexicon baseline (`lexicon-v1`), not a
  trained or statistically validated ML model. The UI and API say so.
- There is no email delivery, password-reset email, or notification system.
- The seeded faculty, students and feedback are demo data created through real
  application flows.
- Preview deployments require a separate `DATABASE_URL` binding if full
  database-backed preview verification is needed.
