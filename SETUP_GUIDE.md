# FacultyInsight AI — Setup Guide

## Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 18 (or Docker)

## 1. Clone / locate repository

`E:\samruddhi\faculty-feedback-system`

## 2. Backend setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt   # Windows
# python -m pip install -r requirements.txt                    # Linux/macOS

cp .env.example .env
```

Environment variables:

| Variable | Purpose |
| --- | --- |
| `APP_ENV` | development / production |
| `API_PREFIX` | default `/api` |
| `JWT_SECRET_KEY` | signing secret (≥ 16 chars) |
| `ACCESS_TOKEN_MINUTES` | token lifetime, default 30 |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | PostgreSQL connection |
| `CORS_ORIGINS` | comma separated allow list |
| `LOGIN_RATE_LIMIT`, `LOGIN_RATE_WINDOW_SECONDS` | login throttling |

## 3. Database setup

```bash
psql "$DATABASE_URL" -f database/schema.sql
psql "$DATABASE_URL" -f database/migrations/001_additive_upgrade.sql
psql "$DATABASE_URL" -f database/seed.sql
```

## 4. Start backend

```bash
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload
```

Health: `GET http://localhost:8000/health`, DB: `GET /health/db`.

## 5. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Vite proxy: `/api` → `http://localhost:8000`.

## 6. Initial admin

- `POST /api/auth/admin/setup` via `http://localhost:5173/setup`, or script `python -m app.scripts.create_admin`.

## 7. Demo data

```bash
cd backend
.venv\Scripts\python.exe -m app.scripts.seed_demo --with-feedback
```

## 8. Running tests

```bash
backend/.venv/bin/python -m pytest backend/tests
cd frontend && npm test && npm run build
```

## 9. Troubleshooting

- JWT secret too short → backend refuses to start.
- Database unreachable → 503 with generic detail.
- Faculty login rejected → approval required.
- Closed period → submissions/edits rejected with 403; reads allowed.
