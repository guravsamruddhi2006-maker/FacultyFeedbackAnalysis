# FacultyInsight AI — Implementation Plan

## Objective

Deliver a production-ready feedback platform for a CSE department with three roles, anonymous feedback, strict multi-faculty separation, real analytics, an explainable NLP baseline, automated tests and reproducible Docker deployment.

## Phase 1 — Database

1. Archive the existing schema and data.
2. Define a canonical PostgreSQL 18 schema with all 12 required tables plus `audit_logs`.
3. Add constraints, checks, foreign keys, indexes and transaction-safe uniqueness rules.
4. Apply an additive migration to the live database (no destructive table/row operations).
5. Seed base master data once. Never recreate subjects each academic year.
6. Add an optional demo seed command using clearly fictional data.

Acceptance: schema applies cleanly to an empty database; migration leaves all existing rows intact.

## Phase 2 — Backend

1. Create `backend/app` with config, database, security, schemas, repositories, services, analytics and API routers.
2. Implement register/login for all roles, first-admin setup, admin-only admin creation and faculty approval.
3. Implement role dependencies that re-check account status on every protected request.
4. Implement catalog CRUD, course offerings and feedback periods.
5. Implement student dashboard, feedback submission/edit with atomic transactions and complete validation.
6. Implement faculty endpoints that derive the faculty ID only from the JWT.
7. Implement admin analytics, comparison, exports and audit logs.
8. Add safe error handling, CORS, security headers and login rate limiting.

Acceptance: OpenAPI docs are complete; every protected endpoint rejects missing/wrong roles; faculty A cannot access faculty B data.

## Phase 3 — Analytics and ML

1. Build Pandas/NumPy aggregation helpers for averages, distributions and trends.
2. Build text cleaning, stopword removal and keyword extraction.
3. Implement a transparent lexicon sentiment baseline with negation handling.
4. Provide a TF-IDF + scikit-learn training script that requires a real labelled CSV, reports accuracy/precision/recall/F1 and a confusion matrix, and persists the model.
5. Use the trained model automatically only if its metadata indicates a valid evaluation.
6. Generate strengths and improvement areas only from question averages and comment evidence.

Acceptance: no hardcoded chart values; sentiment limitations are visible in API responses and documentation.

## Phase 4 — Frontend

1. Create Vite/React/TypeScript with Tailwind and shadcn-style components.
2. Build the auth flow, first-admin setup and role-aware routing.
3. Build admin dashboard and management pages with filters, tables, dialogs and exports.
4. Build faculty dashboard with question, distribution, sentiment and trend charts.
5. Build student dashboard and anonymous feedback form with edit support.
6. Add loading, empty and error states, toasts and destructive confirmations.
7. Ensure responsive desktop/tablet/mobile layouts.

Acceptance: production build succeeds; every button is wired to a real API action.

## Phase 5 — Verification

1. Create an isolated `faculty_feedback_test` database.
2. Add fixtures for admin, two faculty teaching the same subject, students, periods and questions.
3. Test registration, login, hashing, token expiry, role authorization, approval, feedback validation, editing, duplicate prevention, period checks and rollback.
4. Add the critical isolation test and unauthorized-access test.
5. Run backend tests, compile checks and frontend build.
6. Start both applications and exercise the main workflows.
7. Validate Docker Compose configuration/build.

## Phase 6 — Documentation and deployment

1. README with setup, architecture, commands and screenshots placeholders.
2. Database/ER, API, architecture, user manual and deployment docs.
3. `.env.example`, Dockerfiles, Compose, Nginx, health checks and persistent volumes.
4. Production guidance for a low-cost reproducible deployment.
