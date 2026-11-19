# FacultyInsight AI — Architecture

**Version:** 1.0 (recovery baseline + Phase 2 delivery)

## 1. System overview

```
┌──────────────────────────┐         ┌──────────────────────────┐
│  React SPA (Vite)         │  HTTPS  │  FastAPI backend          │
│  localhost:5173           │ ──────▶ │  localhost:8000/api       │
└──────────────────────────┘         └───────────┬──────────────┘
                                                  │ psycopg
                                                  ▼
                                        ┌─────────────────────┐
                                        │  PostgreSQL 18      │
                                        │  faculty_feedback   │
                                        └──────────┬──────────┘
```
## 2. Layered backend design

```
backend/
  app/
    main.py            FastAPI app factory, security headers, CORS, error handlers, health
    core/              config, security (JWT/bcrypt), deps (authN/authZ)
    db/                connection helpers, transactions, fetch helpers
    schemas/           Pydantic models
    services/          audit, insights, reports
    analytics/         SQL aggregations, pandas/numpy engine, lexicon + optional TF-IDF NLP
    api/               routers: auth, catalog, admin, faculty, students, analytics, ml, reports
    scripts/           seed_demo, create_admin
```

- **API layer** (`app/api/*`) validates via Pydantic and enforces role dependencies.
- **Service layer** (`app/services/*`) owns cross-cutting behaviour (audit writes, insight generation, report building).
- **Analytics layer** (`app/analytics/*`) owns calculations; SQL for aggregates, Pandas/Numpy helpers for reusable math, lexicon for sentiment.
- **DB layer** (`app/db/*`) owns connections and transactions; raw parameterised SQL is used (no ORM), which keeps the existing schema and migrations authoritative.

## 3. Authentication and authorisation

- JWT bearer tokens (`sub`, `role`, `iat`, `exp`), HS256 with server secret.
- Passwords hashed with bcrypt; strength validation (min 8, letter + digit, ≤ 72 bytes).
- Login rate limiter per client IP + path.
- Role dependencies: `admin_required`, `faculty_required`, `student_required`, `authenticated`.
- Faculty tokens only resolve approved faculty; pending/rejected are rejected.
- Every faculty data access derives the faculty scope from the JWT subject — never from request body.

## 4. Feedback flow

1. Admin creates/updates academic year, semester, subject, course offering and opens feedback period.
2. Student sees assigned offerings for selected academic year/semester.
3. Student submits ratings (all active questions required, 1–5) + comment (10–1000 chars).
4. DB enforces one submission per (student, offering); edits allowed only while period open (transaction + `FOR UPDATE`).
5. Analytics aggregates answers; insights generated from real averages/comments.

## 5. Frontend structure

```
frontend/src/
  main.tsx, App.tsx, index.css
  components/   Layout, ProtectedRoute, ui
  context/      AuthContext, ToastContext
  hooks/        useApi
  lib/          api client, types, utils
  pages/        AuthPages, Public, student, faculty, admin
```

## 6. Deployment topology

```
nginx (frontend container) -> proxy /api -> backend container -> postgres container
```

See `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, `frontend/nginx.conf`.

## 7. Data flow summary

```
Student submits feedback
  -> POST /api/students/me/feedback (transaction)
     -> feedback + feedback_answer rows
        -> analytics aggregations read answers
           -> insights (strengths/improvements/recommendations/trends)
              -> faculty/admin dashboards + /api/ml/insights
                 -> frontend charts + AI insight panels
                    -> CSV/PDF reports
```

## 8. Non-functional notes

- Security headers on every response (X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy, Cache-Control, HSTS in production).
- Structured 422 validation errors, generic 500 responses, DB-unavailable 503.
- Rate limited auth endpoints.
