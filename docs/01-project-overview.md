# 01 — Project Overview

> **FacultyInsight AI** · Documentation set · [Back to index](../README.md#documentation-index)

## 1.1 What this project is

FacultyInsight AI is a full-stack web application for collecting **anonymous student feedback** about faculty teaching and turning it into **explainable, evidence-based analytics**.

It is built for a single Computer Science and Engineering (CSE) department and supports three roles:

| Role | Signs in with | Primary job |
|------|---------------|-------------|
| **Student** | USN + password | Submit one feedback form per subject offering |
| **Faculty** | Email + password | Choose the subjects they teach, review their own feedback and analytics |
| **Administrator** | Email + password | Manage the catalog, approve accounts and subject requests, open feedback periods, view department analytics |

The system is a real, working application — not a prototype. It has a PostgreSQL schema, a FastAPI backend, a React frontend, automated tests, CSV/PDF report export, audit logging and a production deployment on Vercel + Neon.

## 1.2 The problem it solves

Collecting teaching feedback in a college department is usually done with paper forms or spreadsheets. That approach has recurring problems:

- **Students are not anonymous**, so feedback is biased or withheld.
- **Results are not aggregated** — someone must manually total hundreds of forms.
- **Faculty cannot see their own data** in a timely, private way.
- **There is no audit trail** of who changed what.
- **There is no link** between a subject, the faculty who teaches it, and the feedback for that exact offering.
- **Insights are guesses** — "students seem unhappy" — rather than numbers and quoted themes.

FacultyInsight AI addresses each of these directly.

## 1.3 Objectives

1. Let students submit **structured ratings plus a written comment** exactly once per subject offering.
2. Keep feedback **anonymous to faculty and administrators** while still preventing duplicate submissions.
3. Give **faculty a private view** of only their own subjects, ratings, comments and trends.
4. Give **administrators a department-wide view** for planning and quality review.
5. Produce **transparent analytics**: averages, distributions, question-level scores, trends and theme extraction.
6. Provide **CSV and PDF exports** for offline reporting.
7. Enforce **role-based access control** and record sensitive actions in an **audit log**.
8. Run reliably on free/entry-level infrastructure (Vercel serverless + Neon PostgreSQL).

## 1.4 Feature summary

### Student portal
- Registration with USN, name and department.
- Login with USN + password.
- Dashboard filtered by academic year and semester.
- Per-offering status: **submitted**, **pending** (period open) or **closed**.
- Feedback form with all active questions rated 1–5 and a comment of 10–1000 characters.
- Edit a submission only while the feedback period is open.

### Faculty portal
- Self-registration (account starts as `pending` until an administrator approves it).
- Choose the subjects they teach for a given academic year and semester.
- Request a subject that is missing from the catalog.
- View only their own dashboard, comments, sentiment and trends.
- Download their own CSV/PDF report.
- Change their own password.

### Administrator portal
- First-run setup screen (`/setup`) to create the first administrator.
- Dashboard with department counts, performance by academic year, responses by semester, faculty comparison and question-level averages.
- Manage departments, academic years, subjects, feedback questions and feedback periods.
- Create faculty accounts; approve, reject or deactivate faculty.
- Create, edit and deactivate student accounts.
- Review faculty subject requests.
- View and deactivate other administrator accounts.
- Read the audit log.
- Download department-wide CSV/PDF reports.

### Cross-cutting
- JWT authentication (HS256, 30-minute default lifetime).
- bcrypt password hashing and password-strength rules.
- Per-process login rate limiting.
- Security headers, CORS allow-list, generic error responses.
- Idempotent, additive database migrations that never drop data.
- Automated backend and frontend test suites.

## 1.5 How the pieces fit together

```text
Browser (React SPA)
        │  HTTPS / JSON, Bearer JWT
        ▼
FastAPI application  ──►  Analytics / NLP engine
        │                        │
        │  SQL (psycopg 3)       │  reads aggregates
        ▼                        ▼
PostgreSQL 18 (Neon)  ◄──────────┘
```

- The React app is built to static files and served by Vercel.
- API calls go to the FastAPI app under `/api`.
- FastAPI talks to PostgreSQL with parameterised SQL.
- Analytics are computed from real rows; there is no hardcoded result data.

See [02 — System Architecture](./02-system-architecture.md) for the full picture and the architecture diagram.

## 1.6 What is deliberately *not* claimed

Accuracy matters for a viva and for future maintainers. The project does **not** claim:

- A validated machine-learning model. The active sentiment engine is a transparent **lexicon baseline** (`lexicon-v1`). A TF-IDF classifier exists in `ml/` but its metadata says `"validated": false`, so it is **not active**.
- Real-time chat, email notifications or SMS.
- Multi-department tenancy. The catalog seeds one department and the product is designed around it.
- Automatic faculty-to-subject assignment. Faculty choose their own subjects; administrators approve requests but do not assign teaching loads.
- A mobile app or offline mode.

These boundaries are documented again in [20 — Known Limitations](./20-known-limitations.md).

## 1.7 Repository at a glance

| Path | Purpose |
|------|---------|
| `backend/` | FastAPI application, schemas, services, tests |
| `frontend/` | React + TypeScript + Vite single-page app |
| `database/` | Canonical schema, seed data, additive migrations, backups (ignored) |
| `ml/` | Optional sentiment-training script and labelled sample data |
| `api/index.py` | Vercel serverless entry point |
| `docs/` | This documentation set and diagrams |
| `docker-compose.yml` | Local PostgreSQL + backend + frontend stack |
| `vercel.json` | Vercel build/routing configuration |

## 1.8 Documentation map

| # | Document | Read it when you want to… |
|---|----------|---------------------------|
| 01 | Project overview | Understand the product (this page) |
| 02 | System architecture | See components and request flow |
| 03 | Technology stack | Check exact versions |
| 04 | Project structure | Find a file |
| 05 | Database schema | Understand every table |
| 06 | Migrations and seeding | Set up or upgrade a database |
| 07 | API reference | Call an endpoint |
| 08 | Authentication and authorization | Understand roles and tokens |
| 09 | Student guide | Use the student portal |
| 10 | Faculty guide | Use the faculty portal |
| 11 | Administrator guide | Run the department |
| 12 | Subject selection and requests | Understand the teaching-load rules |
| 13 | Feedback lifecycle | Follow a submission end to end |
| 14 | Analytics and AI | Understand the numbers and NLP |
| 15 | Security and privacy | Review protections and data handling |
| 16 | Installation on Windows | Run it locally |
| 17 | Deployment | Ship it to production |
| 18 | Testing | Run and interpret the test suites |
| 19 | Troubleshooting | Fix a problem |
| 20 | Known limitations | Know what is out of scope |
| 21 | Glossary | Look up a term |
| 22 | Future enhancements | Plan the next iteration |

## 1.9 Status

| Item | Status |
|------|--------|
| Backend tests | 77 passing against a local PostgreSQL test database |
| Frontend tests | 12 passing across 3 files |
| TypeScript + production build | Passing (`npm run build`) |
| Production health endpoint | `GET /health` returns `200` |
| Production URL | `https://faculty-feedback-system-blush.vercel.app` |

Test results are from a local run; see [18 — Testing](./18-testing.md) for exact commands and caveats.

---

**Next:** [02 — System Architecture →](./02-system-architecture.md)
