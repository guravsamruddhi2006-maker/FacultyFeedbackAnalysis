# FacultyInsight AI — Deployment Guide

## 1. Production build

Frontend:

```bash
cd frontend
npm run build
```

Backend runtime: FastAPI + Uvicorn with 4 workers behind a reverse proxy in production.

## 2. Docker Compose (recommended)

```bash
docker compose up --build -d
```

Services:

- `db` — PostgreSQL 18, persistent volume `postgres_data`.
- `backend` — FastAPI container, port `8000`.
- `frontend` — nginx container serving the SPA, port `5173`, proxies `/api` → `backend:8000`.

## 3. Environment

- Backend: `backend/.env` or container environment (`DB_HOST=db`, `DB_PASSWORD`, `JWT_SECRET_KEY`, `CORS_ORIGINS`, `APP_ENV=production`).
- Frontend: `VITE_API_BASE_URL` (defaults to `/api` relative, same-origin through nginx).

## 4. Nginx

`frontend/nginx.conf` serves the SPA with `try_files ... /index.html` and proxies `/api/` to the backend.

## 5. Health checks

- `GET /health` → service ok.
- `GET /health/db` → database connected.

## 6. Production notes

- Use a strong random `JWT_SECRET_KEY`.
- Use TLS termination at the reverse proxy.
- Restrict `CORS_ORIGINS` to the real frontend origin.
- Run database migrations before traffic (schema + additive migration).
- Back up `faculty_feedback` before upgrades.

## 7. Rate limiting in production

- Login rate limiting is implemented as an in-process limiter (`backend/app/core/deps.py`) keyed by client IP + path,
  configurable via `LOGIN_RATE_LIMIT` (default 12) and `LOGIN_RATE_WINDOW_SECONDS` (default 300).
- It returns HTTP 429 with a `Retry-After` header.
- The Docker Compose deployment runs a single backend container (single uvicorn worker), so the in-process limiter is
  sufficient. No Redis-backed store was introduced. If multi-worker deployment is introduced, replace the in-process
  limiter with a Redis-backed or API-gateway-based shared limiter.

## 8. Railway / Render / Fly style notes

- Set `PORT` env for the platform; uvicorn command: `app.main:app --host 0.0.0.0 --port $PORT`.
- Set `DB_HOST` to the managed database host.

## 9. Validation status (2026-11-17)

- `docker compose config` validated successfully (db, backend, frontend).
- Backend/frontend Dockerfiles and nginx config reviewed; runtime image builds could not be executed in the local
  validation environment because the Docker daemon was unavailable. Run `docker compose up --build -d` in an
  environment with a running Docker daemon to build and start the full stack.

## 10. Vercel deployment (FastAPI + static frontend)

- Vercel project uses the FastAPI framework preset; the ASGI app is exposed via the serverless entry `api/index.py`
  (FastAPI instance `app`, served as a Vercel Function).
- The root-level `requirements.txt` is used by the Vercel Python builder (copy of `backend/requirements.txt`).
- The production frontend build (`frontend/dist`, produced by `npm run build` in `frontend/`) is served by the same
  FastAPI function through FastAPI's low-priority frontend routes (`app.frontend("/", directory=..., fallback="auto")`.
  When no API/health route matches, the SPA (with `index.html` fallback) is served; API routes (`/api/*`) and
  `/health*` take precedence.
- Frontend API calls use same-origin `/api` base (`VITE_API_BASE_URL` defaults to `/api`).
- Configure backend env vars on Vercel: `DATABASE_URL` (Neon), `JWT_SECRET_KEY`, `APP_ENV=production`, `DB_*` as needed,
  `CORS_ORIGINS`, and frontend var `VITE_API_BASE_URL=/api`.

## 11. Remaining deployment blockers

- Live Vercel deployment and Neon connectivity require Vercel CLI authentication and Neon credentials, which are not
  available in the current execution environment. Local validation (build + tests + health) is complete; deployment
  itself is pending those credentials.
