# FacultyInsight AI — API Documentation

Base URL: `http://localhost:8000/api` (configurable via `API_PREFIX`).

Interactive docs: `/docs`, `/redoc`; OpenAPI schema: `/openapi.json`; health: `/health`, `/health/db`.

Interactive docs and OpenAPI schema are enabled by default and automatically disabled when `APP_ENV=production`.

All protected endpoints require:

```
Authorization: Bearer <access_token>
```

with a JWT containing `sub`, `role`, `iat`, `exp`.

## 1. Authentication

### `POST /auth/admin/setup`
First-admin bootstrap. Only allowed while `admins` is empty.

### `POST /auth/admin/login`
Body: `{ "email": "...", "password": "..." }`.

### `POST /auth/faculty/register`
Body: `{ "name", "email", "department_id", "password", "confirm_password" }`. Creates faculty with status `pending`.

### `POST /auth/faculty/login`
Body: `{ "email", "password" }`. Rejects pending/rejected/inactive accounts.

### `POST /auth/student/register`
Body: `{ "student_id" (USN), "name", "department_id", "password", "confirm_password" }`.

### `POST /auth/student/login`
Body: `{ "student_id", "password" }`.

### `GET /auth/me`
Returns the current principal (`id`, `role`, `name`, `email`, `department_id`, `status`).

### `POST /auth/change-password`
Body: `{ "current_password", "new_password", "confirm_password" }`.

### `POST /auth/admins`
Admin-only creation of additional admin accounts.

## 2. Catalog

- `GET /catalog/public/departments` — public department list (registration).
- `GET /catalog/departments` — authenticated department list with counts.
- `POST /catalog/departments`, `PUT /catalog/departments/{id}`, `DELETE /catalog/departments/{id}` — admin.
- `GET /catalog/semesters`, `GET /catalog/academic-years`.
- `POST /catalog/academic-years`, `DELETE /catalog/academic-years/{year}` — admin.
- `GET /catalog/subjects?semester_number=&search=`.
- `POST /catalog/subjects`, `PUT /catalog/subjects/{code}`, `DELETE /catalog/subjects/{code}` — admin.
- `GET /catalog/course-offerings?academic_year=&semester_number=&subject_code=&faculty_id=&page=&page_size=`.
- `POST /catalog/course-offerings`, `DELETE /catalog/course-offerings/{offering_id}` — admin.
- `GET /catalog/feedback-questions?include_inactive=`.
- `POST /catalog/feedback-questions`, `PUT /catalog/feedback-questions/{id}`, `DELETE /catalog/feedback-questions/{id}` — admin.
- `GET /catalog/feedback-periods?academic_year=`.
- `PUT /catalog/feedback-periods`, `DELETE /catalog/feedback-periods/{academic_year}/{semester_number}` — admin.

## 3. Student

- `GET /students/me/dashboard?academic_year=&semester_number=` — assigned offerings, statuses, summary.
- `GET /students/me/feedback/{offering_id}` — form data, active questions, existing feedback, `editable`.
- `POST /students/me/feedback` — body `{ "offering_id", "ratings": [{ "question_id", "rating" }], "comment" }`.
- `PUT /students/me/feedback/{feedback_id}` — body same as submit; only while period open and owner.
- `GET /students/me/feedback/{feedback_id}/submission`.
- `GET /students/me/profile`, `POST /students/me/change-password`.

## 4. Faculty

- `GET /faculty/me` — profile, summary, offerings.
- `GET /faculty/me/dashboard?academic_year=&semester_number=&subject_code=`.
- `GET /faculty/me/comments?academic_year=&semester_number=&subject_code=&sentiment=&page=&page_size=`.
- `GET /faculty/me/trends?subject_code=`.
- `GET /faculty/me/offerings`, `GET /faculty/me/filter-options`, `GET /faculty/me/sentiment`.

## 5. Analytics

- `GET /analytics/admin?academic_year=&semester_number=&subject_code=&faculty_id=` — admin dashboard payload.
- `GET /analytics/admin/faculty/{faculty_id}?academic_year=&semester_number=&subject_code=` — admin faculty view (includes insights).
- `GET /analytics/admin/faculty-comparison?subject_code=&academic_year=&semester_number=` — admin.
- `GET /analytics/faculty/me?academic_year=&semester_number=&subject_code=` — faculty own analytics.
- `GET /analytics/faculty/me/comparison?subject_code=` — faculty own comparison.

## 6. AI / ML

- `GET /ml/model-info` — active sentiment engine, validation state, metrics.
- `POST /ml/sentiment` — body `{ "texts": [{ "text": "..." }] }`; returns label, score, confidence, matched terms.
- `GET /ml/insights?academic_year=&semester_number=&subject_code=` — faculty-scoped evidence-based insights.

## 7. Reports

- `GET /reports/faculty/me?format=csv|pdf&academic_year=&semester_number=&subject_code=`.
- `GET /reports/admin?format=csv|pdf&academic_year=&semester_number=&subject_code=&faculty_id=`.

Invalid formats return `422`.

## 8. Error format

Validation errors return `422` with `{ "detail": "Please check the submitted values.", "errors": [{ "field", "message" }] }`.
Operational errors return generic messages; internal errors are logged and returned as `500` without internals.

## 9. Status codes

- `200 OK`, `201 Created`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict`, `422 Unprocessable Entity`, `429 Too Many Requests`, `503 Service Unavailable.
