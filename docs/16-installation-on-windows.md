# 16 — Installation on Windows

> **FacultyInsight AI** · Documentation set · [Back to index](../README.md#documentation-index)

A complete, beginner-friendly setup for Windows 10/11 using PowerShell. Commands assume the repository is at `E:\samruddhi\faculty-feedback-system`; replace that path with yours.

## 16.1 Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| Python | 3.12 | `python --version` |
| Node.js | 20 LTS | `node --version` |
| npm | bundled with Node | `npm --version` |
| PostgreSQL | 18 | `psql --version` |
| Git | any recent | `git --version` |

Install links:

- Python — <https://www.python.org/downloads/windows/> (tick **Add python.exe to PATH**).
- Node.js — <https://nodejs.org/> (LTS).
- PostgreSQL — <https://www.postgresql.org/download/windows/> (remember the `postgres` password).
- Git — <https://git-scm.com/download/win>.

Verify all four in a **new** PowerShell window:

```powershell
python --version
node --version
npm --version
psql --version
```

## 16.2 Get the code

```powershell
cd E:\samruddhi
git clone https://github.com/guravsamruddhi2006-maker/FacultyFeedbackAnalysis.git faculty-feedback-system
cd faculty-feedback-system
```

If you already have the folder, just `cd` into it.

## 16.3 Create the Python environment

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

You should see `(.venv)` at the start of the prompt. Every backend command below assumes the environment is active.

## 16.4 Create the database

Open **SQL Shell (psql)** from the Start menu, or run `psql -U postgres` in PowerShell, then:

```sql
CREATE DATABASE faculty_feedback;
\q
```

Load the schema and seed data:

```powershell
psql -U postgres -d faculty_feedback -f database\schema.sql
psql -U postgres -d faculty_feedback -f database\seed.sql
```

> `seed.sql` creates reference data only. It does **not** create any user account.

## 16.5 Configure environment variables

Copy the template:

```powershell
Copy-Item .env.example .env
```

Open `.env` in an editor and set at least:

```dotenv
APP_ENV=development
JWT_SECRET_KEY=<a random string of at least 32 characters>
DB_HOST=localhost
DB_PORT=5432
DB_NAME=faculty_feedback
DB_USER=postgres
DB_PASSWORD=<your postgres password>
CORS_ORIGINS=http://localhost:5173,http://localhost:4173
```

Generate a strong secret:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Paste the output as `JWT_SECRET_KEY`. Never commit `.env`.

### Notes on configuration

- The backend reads `.env` from the repository root **and** `backend/.env`. Root values win because loading does not override existing keys.
- `API_PREFIX` in `backend/.env.example` is **not read** by the application. The prefix is hardcoded to `/api`.
- For a remote database, set `DATABASE_URL` instead of the individual `DB_*` values.

## 16.6 Start the backend

In terminal 1, with the virtual environment active:

```powershell
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Check:

- <http://localhost:8000/health> → `{"status":"ok",...}`
- <http://localhost:8000/health/db> → `{"status":"ok","database":"connected"}`
- <http://localhost:8000/docs> → interactive API docs (development only)

If the backend cannot reach the database, see [19 — Troubleshooting](./19-troubleshooting.md).

## 16.7 Start the frontend

In terminal 2:

```powershell
cd frontend
npm ci
npm run dev
```

Open <http://localhost:5173>. Vite proxies `/api` to `http://localhost:8000`.

If your backend runs elsewhere:

```powershell
$env:VITE_PROXY_TARGET = "http://localhost:8001"
npm run dev
```

## 16.8 First run

1. Open <http://localhost:5173/setup>.
2. Create the first administrator (name, email, password).
3. Sign in at `/login` with the **Admin** tab.
4. Create faculty accounts or let faculty self-register and approve them.
5. Add subjects/selections and open a feedback period.

The setup endpoint only works while no administrator exists.

## 16.9 Run with Docker (optional)

If you prefer containers:

```powershell
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend (Nginx) | <http://localhost:5173> |
| Backend | <http://localhost:8000> |
| PostgreSQL | `localhost:5432` (internal to compose network) |

The compose file uses development-style credentials (`postgres`/`postgres`, `JWT_SECRET_KEY: change-me-in-production`). **Do not use those values in production.** See [17 — Deployment](./17-deployment.md).

## 16.10 Verify the installation

| Check | Command / URL | Expected |
|-------|---------------|----------|
| Backend health | `GET /health` | `200` |
| Database health | `GET /health/db` | `200`, `database: connected` |
| API docs | `/docs` | Loads in development |
| Frontend | <http://localhost:5173> | Login page |
| Setup | `/setup` | Admin form (first run) |

## 16.11 Everyday commands

```powershell
# activate the environment
.\.venv\Scripts\Activate.ps1

# backend
cd backend
uvicorn app.main:app --reload

# frontend
cd ..\frontend
npm run dev

# production build of the frontend
npm run build

# tests
cd ..\
$env:DATABASE_URL="postgresql://postgres:<local-password>@localhost:5432/faculty_feedback"
$env:TEST_DB_NAME="faculty_feedback_test"
python -m pytest backend\tests -q

cd frontend
npm test
```

See [18 — Testing](./18-testing.md) for why `DATABASE_URL` is cleared for tests.

## 16.12 Common installation errors

| Error | Cause | Fix |
|-------|-------|-----|
| `python` not recognised | Python not on PATH | Reinstall and tick "Add to PATH" |
| `Activate.ps1 cannot be loaded` | Execution policy | `Set-ExecutionPolicy -Scope Process Bypass` |
| `ModuleNotFoundError: app` | Wrong working directory | Run `uvicorn` from `backend/` |
| `connection refused` on 5432 | PostgreSQL not running | Start the service or `docker compose up db` |
| `password authentication failed` | Wrong `DB_PASSWORD` | Update `.env` |
| `relation "faculty" does not exist` | Schema not loaded | Run `database\schema.sql` |
| Frontend calls fail with 404 | Proxy target wrong | Set `VITE_PROXY_TARGET` |
| `npm ci` fails | Lockfile mismatch | Use Node 20; delete `node_modules` and retry |

## 16.13 Uninstall / reset

```powershell
# stop servers with Ctrl+C, then deactivate
deactivate

# remove the virtual environment
Remove-Item -Recurse -Force .venv

# remove frontend dependencies
Remove-Item -Recurse -Force frontend\node_modules

# reset the database (destructive)
psql -U postgres -c "DROP DATABASE faculty_feedback;"
psql -U postgres -c "CREATE DATABASE faculty_feedback;"
psql -U postgres -d faculty_feedback -f database\schema.sql
psql -U postgres -d faculty_feedback -f database\seed.sql
```

## 16.14 Related documents

- [03 — Technology Stack](./03-technology-stack.md)
- [17 — Deployment](./17-deployment.md)
- [18 — Testing](./18-testing.md)
- [19 — Troubleshooting](./19-troubleshooting.md)

---

**Next:** [17 — Deployment →](./17-deployment.md)
