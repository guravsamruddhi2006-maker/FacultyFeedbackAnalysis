# 04 — Project Structure

> **FacultyInsight AI** · Documentation set · [Back to index](../README.md#documentation-index)

This page maps the repository so you can find code quickly.

## 4.1 Top level

```text
faculty-feedback-system/
├── backend/                 FastAPI application
├── frontend/                React + TypeScript SPA
├── database/                Schema, seed, migrations, local backups
├── ml/                      Optional sentiment training assets
├── docs/                    This documentation set + images
├── api/                     Vercel serverless entry point
├── docker-compose.yml       Local three-service stack
├── vercel.json              Vercel build/routing config
├── .env.example             Root environment template
├── README.md                Project entry point
└── *.md                     Historical phase and audit reports
```

The root-level `*.md` files (for example `FINAL_PROJECT_REPORT.md`, `SECURITY_AND_PRIVACY.md`, `API_DOCUMENTATION.md`) are earlier reports kept for history. The maintained documentation is this `docs/` set.

## 4.2 Backend

```text
backend/
├── app/
│   ├── __init__.py              __version__
│   ├── main.py                  App, middleware, routers, health, SPA serving
│   ├── db.py                    Connection helper + get_db dependency
│   ├── schema.py                Idempotent runtime upgrades
│   ├── recover_admin.py         Operator admin recovery CLI
│   ├── core/
│   │   ├── config.py            Settings from environment
│   │   ├── security.py          bcrypt, JWT, password rules
│   │   └── deps.py              Auth dependencies, role guards, rate limiter
│   ├── api/
│   │   ├── auth.py              /auth/*
│   │   ├── catalog.py           /catalog/*
│   │   ├── students.py          /students/me/*
│   │   ├── faculty.py           /faculty/me/*
│   │   ├── admin.py             /admin/*
│   │   ├── analytics.py         /analytics/*
│   │   ├── ml.py                /ml/*
│   │   └── reports.py           /reports/*
│   ├── analytics/
│   │   ├── service.py           SQL aggregation + dashboards
│   │   └── text.py              Sentiment, topics, keywords
│   ├── services/
│   │   ├── insights.py          Strengths, improvements, recommendations
│   │   ├── audit.py             Audit-log writer
│   │   └── report_service.py    CSV/PDF builders
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── admin.py
│   │   ├── faculty.py
│   │   ├── feedback.py
│   │   └── common.py
│   └── scripts/
│       └── set_production_admin_password.py
├── tests/                       pytest suite
├── requirements.txt             Pinned dependencies
├── Dockerfile                   Python 3.12 image
├── .env.example                 Backend environment template
└── pytest.ini / conftest        Test configuration lives in tests/
```

### Key files

| File | Why it matters |
|------|----------------|
| `app/main.py` | Registers routers under `/api`, sets security headers, disables docs in production |
| `app/core/config.py` | All environment settings; note `api_prefix` is hardcoded to `/api` |
| `app/core/deps.py` | Role checks and the in-process login limiter |
| `app/schema.py` | The only code that changes the schema at runtime |
| `app/analytics/text.py` | The active `lexicon-v1` sentiment engine |
| `app/services/report_service.py` | CSV and PDF generation |

## 4.3 Frontend

```text
frontend/
├── src/
│   ├── main.tsx                 App bootstrap
│   ├── App.tsx                  Route table
│   ├── components/
│   │   ├── Layout.tsx           Shell, navigation, change-password modal
│   │   ├── ProtectedRoute.tsx   Role-based route guard
│   │   └── ui.tsx               Buttons, cards, tables, inputs, modal
│   ├── context/
│   │   ├── AuthContext.tsx      Login/logout and stored user
│   │   └── ToastContext.tsx     Notifications
│   ├── hooks/
│   │   └── useApi.ts            Small data-fetching hook
│   ├── lib/
│   │   ├── api.ts               fetch wrapper, token storage, ApiError
│   │   ├── types.ts             Shared TypeScript types
│   │   └── utils.ts             Formatting helpers
│   └── pages/
│       ├── AuthPages.tsx        Login, student/faculty register, admin setup
│       ├── admin/
│       │   ├── AdminDashboard.tsx
│       │   └── AdminManagement.tsx
│       ├── faculty/
│       │   ├── FacultyDashboard.tsx   Overview, comments, analytics
│       │   ├── FacultySubjects.tsx    Selections and requests
│       │   └── FacultyProfile.tsx
│       └── student/
│           ├── StudentDashboard.tsx
│           └── FeedbackForm.tsx
├── package.json
├── vite.config.ts               Dev proxy + Vitest config
├── tailwind.config.js
├── tsconfig.json
├── Dockerfile                   Build + Nginx image
└── nginx.conf                   SPA fallback + /api proxy
```

## 4.4 Database

```text
database/
├── schema.sql                         Canonical 16-table schema
├── seed.sql                           Reference data only (no users)
├── migrations/
│   ├── 001_additive_upgrade.sql       Legacy columns/constraints
│   ├── 002_faculty_subject_selections.sql
│   └── 003_deactivate_backfilled_selections.sql
└── backups/                           Local dumps — git-ignored
```

## 4.5 ML assets

```text
ml/
├── train.py                           Trains and evaluates the optional model
├── data/
│   └── sentiment_labeled.csv          Small labelled sample
└── models/
    ├── sentiment_model_metadata.json  Metrics; "validated": false
    └── sentiment_model.joblib         Serialised pipeline (if trained)
```

The presence of files here does **not** mean a trained model is active. The engine activates the model only when metadata records a completed, validated evaluation. See [14 — Analytics and AI](./14-analytics-and-ai.md).

## 4.6 Documentation

```text
docs/
├── 01-project-overview.md
├── 02-system-architecture.md
├── 03-technology-stack.md
├── 04-project-structure.md
├── 05-database-schema.md
├── 06-migrations-and-seeding.md
├── 07-api-reference.md
├── 08-authentication-and-authorization.md
├── 09-student-guide.md
├── 10-faculty-guide.md
├── 11-administrator-guide.md
├── 12-subject-selection-and-requests.md
├── 13-feedback-lifecycle.md
├── 14-analytics-and-ai.md
├── 15-security-and-privacy.md
├── 16-installation-on-windows.md
├── 17-deployment.md
├── 18-testing.md
├── 19-troubleshooting.md
├── 20-known-limitations.md
├── 21-glossary.md
├── 22-future-enhancements.md
└── images/
    ├── architecture-diagram.png
    ├── database-er-diagram.png
    └── workflow-diagram.png
```

## 4.7 Naming conventions

- **Backend routes** are grouped by role: `/students/me`, `/faculty/me`, `/admin`.
- **SQL** is always parameterised; table and column names are snake_case.
- **Pydantic models** use PascalCase classes and snake_case fields.
- **React components** are PascalCase files exporting named components; pages are lazy-loaded in `App.tsx`.
- **Tests** are named `test_*.py` (backend) and `*.test.tsx` (frontend).

## 4.8 Related documents

- [03 — Technology Stack](./03-technology-stack.md)
- [05 — Database Schema](./05-database-schema.md)
- [16 — Installation on Windows](./16-installation-on-windows.md)

---

**Next:** [05 — Database Schema →](./05-database-schema.md)
