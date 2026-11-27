# AGENTS.md

FacultyInsight AI is a three-tier app: React 18 SPA (`frontend/`) → FastAPI (`backend/app/`) → PostgreSQL 18 (`database/`). Production runs on Vercel + Neon; Docker Compose is the local container path.

## Read this first

- **Current docs:** `README.md` and `docs/01-*` through `docs/22-*`. Root-level `*.md` files (`PHASE*`, `FINAL_*`, `PROJECT_*`, `*_REPORT.md`, etc.) and `docs/implementation-plan.md` are historical/planning artifacts. Some contain stale claims (for example, `API_DOCUMENTATION.md` says `API_PREFIX` is configurable — it is not) and may contain old credentials. Do not treat them as current behaviour.
- **Real backend:** `backend/app/`. The top-level `backend/main.py`, `backend/db.py`, `backend/security.py`, `backend/feedback_periods.py`, and `backend/test_period_logic.py` are legacy standalone scripts (they import `backend.*` and hardcode localhost) and are not wired into the app. Edit `backend/app/` instead.
- **Ignore skill bundles:** `.<tool>/skills/**`, `skills/**`, `data/skills/**`, and their nested `AGENTS.md` files are installed tool skills, not project instructions.

## Commands (PowerShell, from repo root)

```powershell
# Setup
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
cd frontend; npm ci; cd ..

# Backend — must run from backend/ because imports are app.*
cd backend
uvicorn app.main:app --reload --port 8000

# Frontend — Vite on :5173, proxies /api to :8000 (override with VITE_PROXY_TARGET)
cd frontend
npm run dev

# Backend tests (full / one file / one test)
$env:DATABASE_URL="postgresql://postgres:<local-password>@localhost:5432/faculty_feedback"
$env:TEST_DB_NAME="faculty_feedback_test"
python -m pytest backend\tests -q
python -m pytest backend\tests\test_faculty_isolation.py -q
python -m pytest "backend\tests\test_auth.py::test_pending_faculty_token_is_rejected" -q

# Frontend unit tests / typecheck / build
cd frontend
npm test                 # Vitest run
npm test -- src/components/PasswordInput.test.tsx
npm run build            # tsc --noEmit && vite build
npm run lint             # only tsc --noEmit (no ESLint/Prettier in the repo)
npm run test:e2e         # Playwright, separate from Vitest

# Local containers
docker compose up --build
```

## Testing gotchas

- Backend tests need a local PostgreSQL and the `faculty_feedback_test` database. `backend/tests/conftest.py` drops and recreates the `public` schema there — never point `TEST_DB_NAME` at a real database.
- Set `DATABASE_URL` to an explicit **local** URL for the test process. `backend/.env` may contain the production Neon URL, and PowerShell `$env:DATABASE_URL=""` removes the variable instead of blanking it, so dotenv can re-load the remote value. `backend/tests/conftest.py` now refuses non-local hosts before touching the schema.
- Tests create their schema from `database/schema.sql`; loading `seed.sql` first is not required. The `data` fixture seeds deterministic accounts (`admin@test.local`, `alpha@test.local`, student `4UB26CS001`, password `Test@12345`).
- Importing `app.main` calls `settings.validate()`, so **all** backend commands (including pytest) need `JWT_SECRET_KEY` of at least 16 characters in the root `.env` or `backend/.env`.
- Vitest excludes `frontend/e2e/**`. Playwright starts only its own dev server on `:5173`; authenticated E2E specs (`roles.spec.ts`, `e2e/deep/**`) also need the backend running against the isolated test DB seeded with those fixture accounts. Deep specs mutate shared rows (for example, approving pending faculty), so use `npx playwright test --workers=1`; `E2E_BASE_URL` overrides the base URL.
- There is no CI pipeline. Run the commands above manually.

## Environment and config

- `backend/app/core/config.py` loads the root `.env` first, then `backend/.env`, without override — so root values win. `DATABASE_URL` overrides the individual `DB_*` settings.
- `API_PREFIX` is not read; the API is always under `/api`.
- Frontend API base is `VITE_API_BASE_URL` (default `/api`). JWT and cached user live in `localStorage` under `facultyinsight.token` and `facultyinsight.user`; a 401 fires the `facultyinsight:unauthorized` event.
- `APP_ENV=production` disables `/docs`, `/redoc`, and `/openapi.json`, enables HSTS, and refuses a JWT secret containing `change-me`. Because `docker-compose.yml` hardcodes `JWT_SECRET_KEY: change-me-in-production` with `APP_ENV: production`, the stock `docker compose up --build` fails at startup — replace that value in the compose file first.
- If `frontend/dist/` exists, the backend serves the SPA at `/` instead of the JSON health root. `frontend/dist` is gitignored but present after a build, so delete it if you need the root JSON health response.

## Database rules

- `database/schema.sql` defines the 16 core tables. `schema_migrations` is added by migrations/runtime upgrades.
- `database/seed.sql` contains reference data only and creates **no users**. The first administrator is created at `/setup`, or via `python -m app.scripts.create_admin` from `backend/`.
- `database/migrations/` has `001`–`004`; `backend/app/schema.py` applies additional runtime upgrades (for example `004_student_archive_support` and `004_student_enrollment_roster`) on the first database-backed request with an advisory lock and records them in `schema_migrations`.
- Migrations must stay additive and idempotent; never drop or truncate data.
- Gitignored and never to be committed: `.env` / `.env.*` (except `.env.example`), `database/backups/`, `test_db.py`, logs, and `frontend/prod_*_verify.mjs` / `frontend/debug_*.mjs`.

## Product and security invariants

- Three roles: student (USN), faculty (email, must be `approved` before sign-in), and administrator (email).
- Feedback is anonymous. Faculty, admin, analytics, and report queries must never return student IDs. Faculty must only see their own offerings and data. `backend/tests/test_faculty_isolation.py` enforces this — preserve it when editing queries.
- Use parameterised SQL, the existing role guards in `backend/app/core/deps.py`, and `write_audit` for sensitive mutations.
- AI honesty: the active sentiment engine is `lexicon-v1`. The TF-IDF model under `ml/` has `"validated": false` and is inactive. Do not activate it or claim validated ML without real validated metrics.

## Deployment

- Vercel builds the SPA plus `api/index.py` as a Python function (30-second limit) against Neon; `api/index.py` adds `backend/` to `sys.path`, so application code is unchanged.
- Production environment: `DATABASE_URL`, a strong `JWT_SECRET_KEY` (not the example), `APP_ENV=production`, and `CORS_ORIGINS`.
- Docker images target Python 3.12 and Node 20 even if the local `.venv` or Node version differs; keep compatibility with those versions.
