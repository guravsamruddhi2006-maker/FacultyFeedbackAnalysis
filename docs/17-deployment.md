# 17 — Deployment

> **FacultyInsight AI** · Documentation set · [Back to index](../README.md#documentation-index)

The production deployment is **Vercel** (frontend + Python serverless function) with **Neon PostgreSQL 18**. Docker Compose is the alternative for a self-hosted server.

## 17.1 Production topology

```text
GitHub main
    │ push
    ▼
Vercel build
    ├── frontend/dist        (Vite static build)
    └── api/index.py         (FastAPI serverless function, 30 s max)
    │
    ▼
Neon PostgreSQL 18
```

- `vercel.json` sets `framework: fastapi` and `maxDuration: 30` for `api/index.py`.
- `api/index.py` adds `backend/` to `sys.path` and imports `app.main:app`.
- When `frontend/dist` exists, FastAPI serves it with SPA fallback, so deep links work.
- Production URL: <https://faculty-feedback-system-blush.vercel.app>.

## 17.2 Prerequisites

- A GitHub repository containing the project.
- A Vercel account connected to GitHub.
- A Neon project with a PostgreSQL 18 database.
- The database schema and seed loaded (see below).

## 17.3 Prepare the database

In the Neon SQL editor (or with `psql` using the Neon connection string):

1. Run `database/schema.sql`.
2. Run `database/seed.sql`.

The runtime upgrade in `backend/app/schema.py` also applies additive changes on first use, but loading the schema first is the clean path.

> Never run `seed.sql` against a database that already has real data unless you understand it is idempotent reference data. It inserts no users.

## 17.4 Environment variables on Vercel

Set these in **Project → Settings → Environment Variables** for Production (and Preview if desired):

| Variable | Required | Notes |
|----------|----------|-------|
| `DATABASE_URL` | Yes | Neon pooled connection string |
| `JWT_SECRET_KEY` | Yes | 32+ random characters, unique to production |
| `APP_ENV` | Yes | `production` |
| `ACCESS_TOKEN_MINUTES` | No | Default `30` |
| `CORS_ORIGINS` | Recommended | Your production origin(s) |
| `LOGIN_RATE_LIMIT` | No | Default `12` |
| `LOGIN_RATE_WINDOW_SECONDS` | No | Default `300` |

Generate a secret:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Do not reuse the local development secret. Do not commit any of these values.

## 17.5 Deploy

1. Push to `main`.
2. Vercel builds automatically.
3. Confirm the build installs `backend/requirements.txt` and builds `frontend/dist`.
4. Open the deployment URL.

If you deploy manually, ensure the Vercel project root is the repository root and `vercel.json` is present.

## 17.6 Verify the deployment

| Check | Expected |
|-------|----------|
| `GET /health` | `200`, `{"status":"ok",...}` |
| `GET /health/db` | `200`, `{"database":"connected"}` |
| `/docs` | **404/disabled** in production |
| `/setup` | Admin setup if no admin exists |
| Login as admin | Dashboard loads |
| Student flow | Offerings appear after selections + period |

`/health/db` is a quick way to confirm the Neon connection from the serverless function.

## 17.7 First production administrator

1. Open `https://<your-domain>/setup`.
2. Create the administrator.
3. Sign in and verify the dashboard.
4. If a temporary recovery file was used during setup, delete it.

There is no default admin in `seed.sql`.

## 17.8 Updating production

1. Take a Neon backup/snapshot if the change touches data.
2. Merge to `main`.
3. Vercel redeploys.
4. Run `GET /health` and `GET /health/db`.
5. Smoke-test login and one read-only dashboard.

Schema changes must be additive. The runtime upgrade handles new columns/tables on first request.

## 17.9 Rollback

- **Code:** redeploy a previous Vercel deployment from the dashboard.
- **Database:** there are no destructive down-migrations. Restore from a Neon snapshot or a `pg_dump` backup if necessary.
- **Selections/accounts:** deactivate rather than delete.

## 17.10 Docker Compose (self-hosted)

`docker-compose.yml` defines three services:

| Service | Image / build | Port |
|---------|---------------|------|
| `db` | `postgres:18-alpine` | internal 5432 |
| `backend` | `backend/Dockerfile` | `8000:8000` |
| `frontend` | `frontend/Dockerfile` (Nginx) | `5173:80` |

```powershell
docker compose up --build
```

The frontend container serves the built SPA and proxies `/api/` to `http://backend:8000/api/`.

### Before exposing it

- Replace `POSTGRES_PASSWORD: postgres`.
- Replace `JWT_SECRET_KEY: change-me-in-production` with a strong secret.
- Restrict `CORS_ORIGINS` to your real origin.
- Put TLS in front (a reverse proxy or a managed load balancer).
- Do not publish the database port publicly.
- Mount the database volume on durable storage and back it up.

## 17.11 Operational checklist

### Before go-live
- [ ] `APP_ENV=production`
- [ ] Strong `JWT_SECRET_KEY`
- [ ] Neon `DATABASE_URL` set and tested
- [ ] Schema + seed loaded
- [ ] First admin created
- [ ] CORS restricted
- [ ] `/docs` disabled
- [ ] Backup schedule configured

### After go-live
- [ ] `/health` and `/health/db` green
- [ ] Admin login works
- [ ] Faculty approval flow works
- [ ] Student feedback flow works end to end
- [ ] CSV and PDF exports download
- [ ] Audit log records actions

## 17.12 Cost and limits

- Vercel serverless functions have a **30-second** limit here. Large PDF exports or slow Neon cold starts can approach it.
- Neon free tiers may suspend idle databases; the first request after idle can be slower.
- The login rate limiter is per instance, not global.
- Reports are generated in memory; very large departments may need streaming.

## 17.13 Related documents

- [02 — System Architecture](./02-system-architecture.md)
- [06 — Migrations and Seeding](./06-migrations-and-seeding.md)
- [15 — Security and Privacy](./15-security-and-privacy.md)
- [19 — Troubleshooting](./19-troubleshooting.md)

---

**Next:** [18 — Testing →](./18-testing.md)
