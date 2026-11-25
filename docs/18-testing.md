# 18 — Testing

> **FacultyInsight AI** · Documentation set · [Back to index](../README.md#documentation-index)

This page documents the test suites, how to run them, and the results of the last local run.

## 18.1 Test inventory

### Backend (`backend/tests/`)

| File | Focus |
|------|-------|
| `test_auth.py` | Registration, login, token, password rules |
| `test_admin_catalog.py` | Catalog CRUD and constraints |
| `test_admin_recovery.py` | Operator recovery CLI |
| `test_analytics.py` | Analytics endpoints |
| `test_analytics_engine.py` | Aggregation and insight logic |
| `test_faculty_isolation.py` | Faculty can only see their own data |
| `test_faculty_selections.py` | Selection and request rules |
| `test_ml_insights.py` | Sentiment, topics, insights |
| `test_rate_limit.py` | Login limiter |
| `test_reports.py` | CSV/PDF generation |
| `test_student_feedback.py` | Submission, validation, editing |

`conftest.py` creates the schema once per session from `database/schema.sql` and truncates/reseeds between tests.

### Frontend (`frontend/src/`)

| File | Focus |
|------|-------|
| `pages/AuthPages.test.tsx` | Login/registration forms |
| `components/PasswordInput.test.tsx` | Password visibility toggle |
| `components/ProtectedRoute.test.tsx` | Role-based route guard |

Vitest runs in a `jsdom` environment with `@testing-library/react`.

### End-to-end (optional)

`frontend/playwright.config.ts` exists for Playwright. E2E tests are not part of the default suite and require a running stack.

## 18.2 Backend tests

### One-time test database

```powershell
psql -U postgres -c "CREATE DATABASE faculty_feedback_test;"
```

The suite creates its own schema, so it does not need `schema.sql` loaded first.

### Run

From the repository root, with the virtual environment active:

```powershell
$env:DATABASE_URL=""
$env:TEST_DB_NAME="faculty_feedback_test"
python -m pytest backend\tests -q
```

### Why `DATABASE_URL` is cleared

If a developer's `.env` contains a remote production `DATABASE_URL`, the settings object will use it and the suite may hang trying to reach a remote host (or, worse, touch real data). Setting `DATABASE_URL=""` for the test process forces the individual `DB_*` settings, which point at local PostgreSQL.

This is a test-process override only. It does not change `.env` or application code.

### Last local result

```text
77 passed
```

Environment: local PostgreSQL, test database `faculty_feedback_test`. One deprecation warning from Starlette's `TestClient` about `httpx`; it does not affect results.

## 18.3 Frontend tests

```powershell
cd frontend
npm test
```

Or with the compact reporter:

```powershell
npm test -- --reporter=dot
```

### Last local result

```text
Test Files  3 passed (3)
Tests       12 passed (12)
```

A React `act(...)` warning is printed by one auth test. It is a warning, not a failure.

## 18.4 Type check and production build

```powershell
cd frontend
npm run build
```

This runs `tsc --noEmit` and then `vite build`. The last local run completed successfully and produced `frontend/dist`.

## 18.5 Full local verification sequence

```powershell
# 1. backend tests
$env:DATABASE_URL=""
$env:TEST_DB_NAME="faculty_feedback_test"
python -m pytest backend\tests -q

# 2. frontend unit tests
cd frontend
npm test -- --reporter=dot

# 3. type check + build
npm run build
```

Expected: 77 backend tests pass, 12 frontend tests pass, build succeeds.

## 18.6 What the tests cover

| Area | Covered |
|------|---------|
| Registration and login for all roles | Yes |
| Password strength and hashing | Yes |
| JWT issue and rejection | Yes |
| Role isolation (faculty/student) | Yes |
| Catalog CRUD and conflicts | Yes |
| Selection and request rules | Yes |
| Feedback validation and duplicates | Yes |
| Feedback editing window | Yes |
| Analytics and insights | Yes |
| Sentiment and topics | Yes |
| CSV/PDF reports | Yes |
| Rate limiting | Yes |
| Admin recovery | Yes |

## 18.7 What the tests do **not** cover

- Browser rendering beyond the three component tests.
- Real Vercel serverless behaviour (cold starts, 30-second limit).
- Neon network failures.
- Load/performance testing.
- Security scanning or penetration testing.
- Multi-department scenarios (out of scope).

## 18.8 Interpreting failures

| Symptom | Likely cause |
|---------|--------------|
| Tests hang | `DATABASE_URL` points to a remote host — clear it |
| `database ... does not exist` | Create `faculty_feedback_test` |
| `password authentication failed` | Wrong local `DB_PASSWORD` |
| Port/integration errors | Local PostgreSQL not running |
| Frontend test cannot find DOM | `jsdom`/setup file missing |
| Build fails on types | A TypeScript change broke a contract |

## 18.9 Adding a test

### Backend

1. Create `backend/tests/test_<area>.py`.
2. Use the existing fixtures (`client`, authenticated users, seeded data).
3. Assert on status codes and response bodies.
4. Run the full suite, not just the new file, to catch regressions.

### Frontend

1. Create `*.test.tsx` next to the component or in `src/pages`.
2. Render with the providers the component needs (`MemoryRouter`, `ToastProvider`, `AuthProvider`).
3. Use `@testing-library/user-event` for interactions.
4. Run `npm test`.

Do not weaken or skip existing tests to make a change pass. Fix the cause.

## 18.10 CI note

There is no CI pipeline configured in the repository. The commands above are run manually. If you add CI, provision a PostgreSQL service, set `TEST_DB_NAME`, and clear `DATABASE_URL` in the job environment.

## 18.11 Related documents

- [16 — Installation on Windows](./16-installation-on-windows.md)
- [19 — Troubleshooting](./19-troubleshooting.md)
- [20 — Known Limitations](./20-known-limitations.md)

---

**Next:** [19 — Troubleshooting →](./19-troubleshooting.md)
