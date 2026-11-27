# 19 — Troubleshooting

> **FacultyInsight AI** · Documentation set · [Back to index](../README.md#documentation-index)

Symptom → cause → fix. Start with the health checks.

## 19.1 First checks

```powershell
# backend alive?
Invoke-RestMethod http://localhost:8000/health

# database reachable?
Invoke-RestMethod http://localhost:8000/health/db

# is PostgreSQL listening?
Test-NetConnection localhost -Port 5432 -InformationLevel Quiet
```

In production, replace `localhost:8000` with your domain.

## 19.2 Startup and environment

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: app` | Running from the wrong directory | `cd backend` before `uvicorn app.main:app` |
| `JWT_SECRET_KEY must be at least 16 characters` | Secret missing/short | Set a 32+ character value in `.env` |
| `Refusing to start with a placeholder JWT secret` | `APP_ENV=production` with a weak secret | Set a real secret |
| `Activate.ps1 cannot be loaded` | PowerShell execution policy | `Set-ExecutionPolicy -Scope Process Bypass` |
| `python` not found | Python not on PATH | Reinstall with "Add to PATH" |
| Port 8000 already in use | Another process | `uvicorn ... --port 8001` |

## 19.3 Database connection

| Symptom | Cause | Fix |
|---------|-------|-----|
| `connection refused` | PostgreSQL not running | Start the service or `docker compose up db` |
| `password authentication failed` | Wrong `DB_PASSWORD` | Correct `.env` |
| `database "faculty_feedback" does not exist` | DB not created | `CREATE DATABASE faculty_feedback;` |
| `relation "..." does not exist` | Schema not loaded | Run `database\schema.sql` |
| `503` from the API | DB unreachable from the server | Check `DATABASE_URL` / Neon status |
| Tests hang or refuse to start | `.env` points at a remote DB | Set `DATABASE_URL` to an explicit local URL for the test process |
| `too many connections` | Pool exhausted on Neon | Use the pooled connection string |

### Verify the resolved settings safely

```powershell
$env:PYTHONPATH="backend"
python -c "from app.core.config import settings; print(settings.db_host, settings.db_name, bool(settings.database_url))"
```

Do not print passwords.

## 19.4 Authentication

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Invalid credentials` | Wrong identifier/password | Re-check; note students use USN, others email |
| `Account is pending approval` | Faculty not approved | Admin approves in `/admin/faculty` |
| `Account is inactive` | Deactivated | Admin reactivates |
| `401` on every request | Token expired or malformed | Sign in again |
| `403` | Wrong role for the route | Use the correct portal |
| `429` on login | Rate limit hit | Wait for the window (default 300 s) |
| Setup page says complete | An admin already exists | Use login or the recovery CLI |

## 19.5 Students see no offerings

Check, in order:

1. **Faculty approved?** `status = 'approved'`.
2. **Active selection?** A `faculty_subject_selections` row with `is_active = TRUE` for the same subject, year and semester.
3. **Offering exists?** Adding a selection creates it.
4. **Period exists and is open?** `feedback_periods` for that year + semester, with `now` between the dates.
5. **Right filters?** The student must select the matching year and semester.

If the offering shows `closed`, the period is missing or ended.

## 19.6 Feedback submission

| Symptom | Cause | Fix |
|---------|-------|-----|
| Form will not submit | A question is unrated | Rate all questions |
| `Comment must be at least 10 characters` | Too short | Lengthen the comment |
| `409` | Already submitted | Edit the existing submission |
| `403` | Period closed | Check the period dates |
| `404` | Offering not visible | Re-check selections and approval |
| `422` with `errors` | A field failed validation | Read the field messages |

## 19.7 Subject selections

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Semester does not match the subject` | Selected semester differs from the catalog | Use the subject's semester |
| `Selection already exists` | Duplicate tuple | Edit the existing row |
| `409` when editing | Offering already has feedback | Deactivate and add a new selection |
| `Subject not found` | Not in the catalog | Submit a subject request |
| Request rejected as duplicate | A pending request exists | Wait for review |
| Approved request but no offering | Approval only adds to catalog | Add the selection yourself |

## 19.8 Frontend

| Symptom | Cause | Fix |
|---------|-------|-----|
| Blank page after deploy | SPA fallback missing | Ensure FastAPI serves `frontend/dist` or the host rewrites to `index.html` |
| API calls go to the wrong host | `VITE_API_BASE_URL` unset/misconfigured | Set it, or rely on `/api` |
| CORS error | Origin not in `CORS_ORIGINS` | Add the exact origin (scheme + host + port) |
| `npm ci` fails | Lockfile/Node mismatch | Use Node 20; remove `node_modules` and retry |
| Build type error | Contract change | Fix the type, do not disable `tsc` |
| Charts empty | No data for the filters | Try a wider filter |

## 19.9 Reports

| Symptom | Cause | Fix |
|---------|-------|-----|
| PDF download times out on Vercel | 30-second function limit | Narrow filters or generate offline |
| CSV opens with odd characters | Excel encoding | Import as UTF-8 |
| Report has no rows | Filters exclude everything | Widen the filters |
| `403` | Wrong role | Faculty use `/reports/faculty/me`; admins `/reports/admin` |

## 19.10 Administrator recovery

### No admin can sign in, database access available

```powershell
cd backend
python -m app.recover_admin --list
python -m app.recover_admin --email admin@college.edu --name "Administrator"
python -m app.recover_admin --email admin@college.edu --reset
```

`--reset` requires typing `RESET` and a hidden new password.

### Existing admin session, no DB access

```powershell
cd backend
python -m app.scripts.set_production_admin_password --email admin@college.edu
```

It uses the public HTTPS API, never prints the password, and deletes the temporary recovery file after success.

### The recovery file

If a temporary file such as `C:\Users\<you>\.facultyinsight-admin-recovery.txt` exists, delete it after the password change is confirmed. It contains a credential.

## 19.11 Deployment issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| `500` on first request after idle | Neon cold start / DB waking | Retry; check `/health/db` |
| `/docs` is 404 in production | Intended | Use development for docs |
| Function timeout | Heavy report or slow DB | Narrow the request |
| Old frontend after deploy | CDN cache | Hard refresh / redeploy |
| Env var not applied | Set for the wrong environment | Set it for Production and redeploy |

## 19.12 Logs

- Backend logs include method, path, status, duration and request ID.
- `X-Request-ID` is returned to the client and can be matched to a log line.
- Database errors are logged server-side and returned as generic messages.
- Vercel: **Deployments → Functions → Logs**.
- Docker: `docker compose logs backend`.

## 19.13 Reset procedures

### Reset a local database (destructive)

```powershell
psql -U postgres -c "DROP DATABASE faculty_feedback;"
psql -U postgres -c "CREATE DATABASE faculty_feedback;"
psql -U postgres -d faculty_feedback -f database\schema.sql
psql -U postgres -d faculty_feedback -f database\seed.sql
```

### Reset the frontend

```powershell
cd frontend
Remove-Item -Recurse -Force node_modules, dist
npm ci
npm run build
```

## 19.14 When to escalate

Escalate to the maintainer when:

- data appears lost or corrupted;
- a migration fails partway;
- you suspect a credential leak;
- the production database is unreachable for more than a few minutes;
- you find a security vulnerability.

Include the request ID, timestamp, endpoint, status code and redacted logs. Never include passwords, tokens or personal data.

## 19.15 Related documents

- [16 — Installation on Windows](./16-installation-on-windows.md)
- [17 — Deployment](./17-deployment.md)
- [18 — Testing](./18-testing.md)
- [20 — Known Limitations](./20-known-limitations.md)

---

**Next:** [20 — Known Limitations →](./20-known-limitations.md)
