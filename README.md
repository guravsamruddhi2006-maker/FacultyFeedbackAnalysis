# FacultyInsight AI

**AI-Powered Faculty Feedback Management and Teaching Performance Analysis System**

FacultyInsight AI is a full-stack web application that lets a department collect structured,
anonymous faculty feedback from students, analyse real rating data with transparent statistics
and explainable AI/NLP, and turn the findings into actionable teaching improvement insights.

The application supports three roles — **student**, **faculty** and **admin** — with role-based
authentication, a complete feedback lifecycle, aggregated analytics, an AI insight layer, report
exports and audit logging.

---

## Table of contents

1. [Features](#features)
2. [Technology stack](#technology-stack)
3. [Architecture](#architecture)
4. [Getting started](#getting-started)
5. [Database](#database)
6. [API overview](#api-overview)
7. [AI / ML](#ai--ml)
8. [Reports and exports](#reports-and-exports)
9. [Testing](#testing)
10. [Deployment](#deployment)
11. [Documentation index](#documentation-index)

## Features

### Student portal

- Sign in with **USN + password** (student accounts use the college USN as identifier).
- Dashboard showing department, semester, academic year, assigned subjects, faculty names,
  pending and completed feedback.
- Submit feedback for an assigned course offering.
- Rate all five active feedback questions on a 1–5 scale with descriptive labels
  (Very Poor … Excellent).
- Optional written comment (10–1000 characters).
- Edit the submission while the feedback period is open; read-only afterwards.
- One submission per student per course offering per feedback period (database unique constraint).

### Faculty portal

- Faculty registration requires **administrator approval** before sign-in.
- Teaching dashboard with response counts, average rating, rating distribution, question-wise
  performance, subject summaries and academic-year comparison.
- Anonymous student comments with sentiment labelling and topic extraction.
- Evidence-based **strengths** and **improvement areas** (only with a minimum number of responses).
- AI-generated insights and actionable recommendations traceable to aggregated data.

### Admin portal

- Initial admin setup (`/setup`) and admin creation.
- Faculty approval / rejection / deactivation.
- Student management (create, update, audited submission metadata view).
- Department, subject, course-offering, academic-year, feedback-period and feedback-question management.
- Department analytics, faculty performance views, audit log.

### Platform-wide

- JWT access tokens (HS256, configurable expiry), bcrypt password hashing, login rate limiting,
  security headers, CORS allow-list, Pydantic validation, safe error handling, OpenAPI/Swagger docs.
- Audit log for administrative and sensitive actions.
- CSV and PDF reports with role restrictions.

## Technology stack

| Layer | Technology |
| --- | --- |
| Frontend | React 18, TypeScript, Vite 6, Tailwind CSS 3, React Router 6, Recharts, Lucide React, React Hook Form + Zod, Vitest + Testing Library |
| Backend | Python 3.12, FastAPI, Pydantic v2, Uvicorn, psycopg (PostgreSQL driver), JWT (PyJWT), bcrypt, Slow login limiter |
| Analytics | Pandas, NumPy, Matplotlib, scikit-learn, reportlab |
| Database | PostgreSQL 18 |
| Tests | pytest, httpx (FastAPI TestClient), pytest fixtures against an isolated database |

## Architecture

```
frontend (React + Vite)  ->  REST API (FastAPI)  ->  PostgreSQL (psycopg/SQL)
                                    |
                                    +--- app.core (config, security, deps)
            +-------------------+--- app.schemas (Pydantic)
            |                   +--- app.services (audit, insights, reports)
            +--- app.api (auth, catalog, admin, faculty, students, analytics, ml, reports)
            +--- app.analytics (SQL aggregations, Pandas/Numpy engine, lexicon + optional TF-IDF NLP)
            +--- app.db (connection helpers, transactions)
```

- Backend source: `backend/app/`
- Database: `database/schema.sql`, `database/migrations/001_additive_upgrade.sql`, `database/seed.sql`
- ML: `ml/train.py`, `ml/data/sentiment_labeled.csv`, `ml/models/`

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full design.

## Getting started

Prerequisites: Python 3.12, Node 20, PostgreSQL 18.

```bash
# 1. Backend dependencies
backend/.venv/bin/python -m pip install -r backend/requirements.txt

# 2. Configure environment
cp backend/.env.example backend/.env      # then set real values
cp .env.example .env

# 3. Apply database schema (development database faculty_feedback)
psql "$DATABASE_URL" -f database/schema.sql
psql "$DATABASE_URL" -f database/migrations/001_additive_upgrade.sql
psql "$DATABASE_URL" -f database/seed.sql

# 4. Run backend
backend/.venv/bin/python -m uvicorn app.main:app --app-dir backend --reload

# 5. Run frontend
cd frontend
npm install
npm run dev

# 6. Run backend tests
backend/.venv/bin/python -m pytest backend/tests

# 7. Run frontend tests
cd frontend
npm test
```

Default local accounts (after seeding):

| Role | Identifier | Password |
| --- | --- | --- |
| Admin | admin@facultyinsight.local | Admin@12345 |
| Faculty | ravi.demo@facultyinsight.local | Demo@12345 |
| Student | 4UB26CS001 | Demo@12345 |

## Database

The canonical schema lives in `database/schema.sql` and contains:

- `departments`, `academic_years`, `semesters`, `subjects`
- `faculty`, `students`, `admins`
- `course_offerings`, `feedback_periods`, `feedback_questions`, `feedback`, `feedback_answer`
- `audit_logs`

Semesters 1–8 exist; Semester 8 is internship-only and no subjects are seeded for it.

See [DATABASE_DOCUMENTATION.md](DATABASE_DOCUMENTATION.md).

## API overview

Base path: `/api`

| Area | Key endpoints |
| --- | --- |
| Health | `GET /health`, `GET /health/db` |
| Auth | `POST /auth/admin/setup`, `POST /auth/admin/login`, `POST /auth/faculty/register`, `POST /auth/faculty/login`, `POST /auth/student/register`, `POST /auth/student/login`, `GET /auth/me`, `POST /auth/change-password`, `POST /auth/admins` |
| Catalog | `GET /catalog/public/departments`, `GET /catalog/departments`, CRUD `/catalog/subjects`, `/catalog/course-offerings`, `/catalog/feedback-periods`, `/catalog/feedback-questions`, `GET /catalog/semesters`, `GET /catalog/academic-years` |
| Student | `GET /students/me/dashboard`, `GET /students/me/feedback/{offering_id}`, `POST /students/me/feedback`, `PUT /students/me/feedback/{feedback_id}`, `GET /students/me/feedback/{feedback_id}/submission`, `GET /students/me/profile`, `POST /students/me/change-password` |
| Faculty | `GET /faculty/me`, `GET /faculty/me/dashboard`, `GET /faculty/me/comments`, `GET /faculty/me/trends`, `GET /faculty/me/offerings`, `GET /faculty/me/filter-options`, `GET /faculty/me/sentiment` |
| Analytics | `GET /analytics/admin`, `GET /analytics/admin/faculty/{faculty_id}`, `GET /analytics/admin/faculty-comparison`, `GET /analytics/faculty/me`, `GET /analytics/faculty/me/comparison` |
| AI / ML | `GET /ml/model-info`, `POST /ml/sentiment`, `GET /ml/insights` |
| Reports | `GET /reports/faculty/me`, `GET /reports/admin` |
| Admin | `GET /admin/dashboard`, `GET /admin/faculty`, `POST /admin/faculty`, `PATCH /admin/faculty/{faculty_id}/status`, `GET /admin/students`, `POST /admin/students`, `PATCH /admin/students/{student_id}`, `GET /admin/students/{student_id}`, `GET /admin/analytics/faculty/{faculty_id}`, `GET /admin/analytics/faculty-comparison`, `GET /admin/audit-logs`, `GET /admin/admins`, `PATCH /admin/admins/{admin_id}/status` |

Interactive API docs: `http://localhost:8000/docs` and `/redoc`, OpenAPI schema at `/openapi.json`. Available when `APP_ENV=development`; automatically disabled when `APP_ENV=production`.

## AI / ML

- Sentiment: transparent lexicon baseline (`lexicon-v1`) with negation handling and intensity
  modifiers; optional TF-IDF + scikit-learn classifier used only when a validated trained model and
  evaluation metadata are present (`ml/train.py`, `ml/models/`).
- Topics: keyword bucket classification over feedback comments.
- Strengths / improvement areas: statistical thresholds on question averages with minimum response
  counts; every finding carries an evidence string.
- Recommendations: data-driven actions mapped from the lowest-performing question areas.
- Trends: same-faculty academic-year comparisons with change detection.

See [AI_ML_DOCUMENTATION.md](AI_ML_DOCUMENTATION.md).

## Reports and exports

- Faculty report: CSV/PDF (`/api/reports/faculty/me?format=csv|pdf`).
- Admin department report: CSV/PDF (`/api/reports/admin?format=csv|pdf`).
- Reports contain aggregates and anonymised comments only.

## Testing

```bash
# Backend (isolated faculty_feedback_test database)
backend/.venv/bin/python -m pytest backend/tests

# Frontend
cd frontend
npm test
npm run build
```

## Deployment

```bash
docker compose up --build
```

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md).

## Documentation index

- [PROJECT_PROGRESS.md](PROJECT_PROGRESS.md)
- [PROJECT_AUDIT.md](PROJECT_AUDIT.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [DATABASE_DOCUMENTATION.md](DATABASE_DOCUMENTATION.md)
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- [AI_ML_DOCUMENTATION.md](AI_ML_DOCUMENTATION.md)
- [SETUP_GUIDE.md](SETUP_GUIDE.md)
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- [TESTING_DOCUMENTATION.md](TESTING_DOCUMENTATION.md)
- [SECURITY_AND_PRIVACY.md](SECURITY_AND_PRIVACY.md)
- [CHALLENGES_AND_SOLUTIONS.md](CHALLENGES_AND_SOLUTIONS.md)
- [FINAL_PROJECT_REPORT.md](FINAL_PROJECT_REPORT.md)
