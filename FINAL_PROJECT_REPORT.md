# FacultyInsight AI — Final Project Report

**Project:** FacultyInsight AI – AI-Powered Faculty Feedback Management and Teaching Performance Analysis System
**Repository:** `E:\samruddhi\faculty-feedback-system`
**Report date:** 2026-11-16

## 1. Implemented features

### Authentication and roles

- Admin setup (first admin), admin login, admin creation.
- Faculty self-registration with admin approval workflow (pending → approved/rejected/inactive).
- Faculty login, student login by USN, current user endpoint, change password.
- JWT access tokens (HS256, 30 min), bcrypt password hashing, login rate limiting, security headers, CORS allow-list.

### Feedback lifecycle

- Feedback periods per academic year + semester with open/closed windows.
- Student dashboard: assigned offerings, pending/completed/closed statuses.
- Feedback submission with all active questions required (1–5) and comment (10–1000 chars).
- Duplicate submission prevention, atomic editing, closed-period enforcement, ownership checks.

### Analytics

- Faculty dashboard: response count, average rating, rating distribution, question stats, subject summary, year trend, comments, strengths, improvement areas, insights, trend insights.
- Admin dashboard: counts, submission coverage, faculty performance, semester/year analytics, question stats, insights, sentiment.

### AI / ML

- Lexicon sentiment baseline with negation/intensifier handling.
- Optional TF-IDF + scikit-learn classifier via `ml/train.py` (labelled CSV, stratified split, metrics, confusion matrix, model/metadata persistence), activated only with validated metadata.
- Topic extraction, strengths/improvement thresholds (3+ responses), recommendations, trend insights.

### Reports

- Faculty CSV/PDF, admin CSV/PDF via reportlab; faculty CSV via csv module.

### Frontend

- Public landing (`/`) and about (`/about`) pages.
- Student dashboard + feedback form (ratings, comment, edit, read-only closed).
- Faculty dashboard (charts, insights, comments, export), faculty profile.
- Admin dashboard + management pages (faculty, students, catalog, audit).
- Loading/empty/error states, toasts, modals, tables, Recharts charts, export buttons.

### Infra/docs

- Backend requirements, env templates, Docker, compose, nginx config, health endpoints.
- Full documentation set.

## 2. Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md). Backend layered FastAPI (`app/main`, `core`, `schemas`, `services`, `analytics`, `api`, `db`); frontend React SPA; PostgreSQL 18 persistence; pandas/numpy/matplotlib analytics engine; scikit-learn NLP.

## 3. Database structure

See [DATABASE_DOCUMENTATION.md](DATABASE_DOCUMENTATION.md). 12 application tables + audit log, canonical schema + additive migration + seed.

## 4. API endpoints

~40 endpoints across auth/catalog/admin/faculty/students/analytics/ml/reports; full list in [API_DOCUMENTATION.md](API_DOCUMENTATION.md).

## 5. AI/ML methodology

- Lexicon baseline: tokenisation, stopwords, negation, intensifiers, heuristic confidence.
- Trained model path: TF-IDF + Logistic Regression, labelled data, stratified split, macro F1/accuracy/P/R, confusion matrix, metadata.
- Insights: averages + response thresholds; recommendations from lowest areas.

## 6. Test results

- Backend: `pytest backend/tests` → **51 passed**, 0 failed (48 pre-existing + 3 new login rate-limit tests; includes analytics engine, ML insights, model info tests). Final verification run on 2026-11-17: **51 passed**, 0 failed (1 Starlette `httpx` deprecation warning).
- Frontend: `vitest run` → **4 passed**, 0 failed; `npm run build` → **passed** (`tsc --noEmit` + Vite build). Final verification run: **vitest 4 passed, build passed**.
- Browser E2E: Playwright + Chromium headless (`npx playwright test`): **9 passed**, 0 failed (public pages 2, auth guards 4, authenticated local demo logins 3).
- Live runtime (final check): backend uvicorn started, `GET /health` 200, `GET /health/db` 200, OpenAPI 200; protected endpoints returned 401 without token; public catalog endpoint 200. Backend process stopped after verification.

## 7. Build results

- Frontend production build: **passed** (Vite + tsc).
- Backend imports and serves; OpenAPI generated successfully.

## 8. Security measures

- bcrypt, JWT, rate limit, security headers, CORS, Pydantic, safe errors, param queries, audit logs, privacy rules.

## 9. Deployment instructions

- `docker compose up --build` with db/backend/frontend services.

## 10. Known limitations

- Login rate limiter is in-process (single worker); multi-worker deployments should back it with Redis or an API gateway. Docker Compose targets a single backend container, so no Redis was introduced.
- JWT stateless (short expiry).
- Sentiment baseline vs trained model status documented (demo training produced `validated: false`; lexicon baseline active).
- Browser E2E covers public pages and unauthenticated route guards (Playwright, 6/6 passing); authenticated deep workflows are covered by backend/frontend component tests and pending real-credential browser runs.
- Real labelled production sentiment dataset not yet supplied.

## 11. Remaining work

- Authenticated browser E2E runs (student/faculty/admin flows) once real credentials are available.
- Multi-worker Redis-backed rate limiting if deployment scale changes.
- Richer trained sentiment model with real labelled data.
- Additional admin/faculty UI polish.

## 12. Acceptance criteria mapping

1–24 mostly verified by automated tests and runtime checks; final end-to-end acceptance to be run in a live environment (browser-driven flows end-to-end).

See [FINAL_ACCEPTANCE_REPORT.md](FINAL_ACCEPTANCE_REPORT.md) for the final acceptance verdict.
