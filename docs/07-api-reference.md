# 07 — API Reference

> **FacultyInsight AI** · Documentation set · [Back to index](../README.md#documentation-index)

All application endpoints are served under the base path **`/api`**. Authentication uses a Bearer JWT:

```http
Authorization: Bearer <token>
```

The interactive OpenAPI docs are available at `/docs` in development only. They are disabled when `APP_ENV=production`.

## 7.1 Conventions

| Item | Value |
|------|-------|
| Base URL (local) | `http://localhost:8000/api` |
| Base URL (production) | `https://faculty-feedback-system-blush.vercel.app/api` |
| Content type | `application/json` (reports return `text/csv` or `application/pdf`) |
| Auth header | `Authorization: Bearer <JWT>` |
| Token lifetime | 30 minutes by default |
| Validation error | `422` with `detail` and a field-level `errors` array |
| Unauthorized | `401` |
| Forbidden (wrong role) | `403` |
| Not found | `404` |
| Conflict (duplicate/constraint) | `409` |
| Rate limited | `429` |

Role columns below use: **Public** (no token), **Any** (any signed-in user), **Student**, **Faculty**, **Admin**.

## 7.2 Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | Public | Liveness probe |
| `GET` | `/health/db` | Public | Checks `SELECT 1` against the database |

```json
GET /health
{ "status": "ok", "service": "facultyinsight-api", "version": "1.0.0" }
```

## 7.3 Authentication — `/api/auth`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/setup-status` | Public | Whether first-run admin setup is still available |
| `POST` | `/admin/setup` | Public | Create the first administrator (only if none exists) |
| `POST` | `/admin/login` | Public | Administrator login |
| `POST` | `/faculty/register` | Public | Faculty self-registration (`pending`) |
| `POST` | `/faculty/login` | Public | Faculty login (approved accounts only) |
| `POST` | `/student/register` | Public | Student registration |
| `POST` | `/student/login` | Public | Student login |
| `GET` | `/me` | Any | Current user profile |
| `POST` | `/change-password` | Any | Change own password |
| `POST` | `/admins` | Admin | Create another administrator |

### `POST /auth/student/register`

```json
{
  "student_id": "1RV21CS001",
  "name": "Asha Rao",
  "department_id": 1,
  "password": "StrongPass1",
  "confirm_password": "StrongPass1"
}
```

Response `201`:

```json
{ "message": "Student account created. You can sign in now." }
```

### `POST /auth/faculty/register`

```json
{
  "name": "Dr. Meera Iyer",
  "email": "meera.iyer@college.edu",
  "department_id": 1,
  "password": "StrongPass1",
  "confirm_password": "StrongPass1"
}
```

Response `201` with a message explaining that an administrator must approve the account.

### `POST /auth/{role}/login`

`role` is `admin`, `faculty` or `student`. Student login uses `student_id`; faculty and admin login use `email`.

```json
// student
{ "student_id": "1RV21CS001", "password": "StrongPass1" }

// faculty / admin
{ "email": "meera.iyer@college.edu", "password": "StrongPass1" }
```

Response `200`:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_at": "2026-01-01T12:30:00+00:00",
  "user": {
    "id": "1",
    "role": "faculty",
    "name": "Dr. Meera Iyer",
    "email": "meera.iyer@college.edu",
    "department_id": 1,
    "status": "approved"
  }
}
```

### `GET /auth/me`

Returns the current principal. Shape matches the `user` object above.

### `POST /auth/change-password`

```json
{
  "current_password": "StrongPass1",
  "new_password": "StrongerPass2",
  "confirm_password": "StrongerPass2"
}
```

## 7.4 Catalog — `/api/catalog`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/public/departments` | Public | Department list for registration |
| `GET` | `/departments` | Any | All departments |
| `POST` | `/departments` | Admin | Create department |
| `PUT` | `/departments/{id}` | Admin | Update department |
| `DELETE` | `/departments/{id}` | Admin | Delete department (409 if referenced) |
| `GET` | `/semesters` | Any | Semester numbers 1–8 |
| `GET` | `/academic-years` | Any | Academic years |
| `POST` | `/academic-years` | Admin | Add academic year (`YYYY-YY`) |
| `DELETE` | `/academic-years/{year}` | Admin | Delete academic year (409 if referenced) |
| `GET` | `/subjects` | Any | Subjects (optional `semester_number`, `search`) |
| `POST` | `/subjects` | Admin | Create subject |
| `PUT` | `/subjects/{code}` | Admin | Update subject |
| `DELETE` | `/subjects/{code}` | Admin | Delete subject (409 if used) |
| `GET` | `/course-offerings` | Any | Read-only offerings list with filters |
| `GET` | `/feedback-questions` | Any | Active questions; admins may pass `include_inactive=true` |
| `POST` | `/feedback-questions` | Admin | Create question |
| `PUT` | `/feedback-questions/{id}` | Admin | Update question |
| `DELETE` | `/feedback-questions/{id}` | Admin | Delete question (409 if answered) |
| `GET` | `/feedback-periods` | Any | Feedback periods |
| `PUT` | `/feedback-periods` | Admin | Create or update a period |
| `DELETE` | `/feedback-periods/{year}/{semester}` | Admin | Delete a period |
| `POST` | `/bootstrap` | Admin | Idempotently insert base reference data |

### Examples

```json
POST /api/catalog/subjects
{ "subject_code": "CS501", "subject_name": "Machine Learning", "semester_number": 5 }
```

```json
PUT /api/catalog/feedback-periods
{
  "academic_year": "2025-26",
  "semester_number": 5,
  "start_date": "2026-01-10T00:00:00Z",
  "end_date": "2026-01-25T23:59:59Z"
}
```

`GET /catalog/course-offerings` accepts `academic_year`, `semester_number`, `subject_code`, `faculty_id`, `page` and `page_size` (max 100).

## 7.5 Student — `/api/students/me`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/profile` | Student | Own profile |
| `GET` | `/dashboard` | Student | Offerings and submission status |
| `GET` | `/feedback/{offering_id}` | Student | Feedback form data for an offering |
| `POST` | `/feedback` | Student | Submit feedback |
| `PUT` | `/feedback/{feedback_id}` | Student | Edit feedback while the period is open |
| `GET` | `/feedback/{feedback_id}/submission` | Student | Read an existing submission |
| `POST` | `/change-password` | Student | Change own password |

### `GET /students/me/dashboard`

Query: `academic_year`, `semester_number`.

```json
{
  "student": { "student_id": "1RV21CS001", "name": "Asha Rao" },
  "filter_options": {
    "academic_years": ["2025-26", "2026-27"],
    "semesters": [1, 2, 3, 4, 5, 6, 7, 8],
    "periods": [
      { "semester_number": 5, "start_date": "...", "end_date": "...", "is_open": true }
    ]
  },
  "selected": { "academic_year": "2025-26", "semester_number": 5 },
  "offerings": [
    {
      "offering_id": 12,
      "subject_code": "CS501",
      "subject_name": "Machine Learning",
      "faculty_name": "Dr. Meera Iyer",
      "status": "pending",
      "feedback_id": null,
      "period_open": true
    }
  ],
  "summary": { "submitted": 0, "pending": 1, "closed": 0, "total": 1 }
}
```

### `POST /students/me/feedback`

```json
{
  "offering_id": 12,
  "ratings": [
    { "question_id": 1, "rating": 5 },
    { "question_id": 2, "rating": 4 },
    { "question_id": 3, "rating": 4 },
    { "question_id": 4, "rating": 5 },
    { "question_id": 5, "rating": 4 }
  ],
  "comment": "Clear explanations and useful lab examples throughout the semester."
}
```

Rules enforced by the server:

- the offering must be visible to the student (active selection + approved faculty);
- the feedback period must be open;
- every active question must be rated exactly once, 1–5;
- the comment must be 10–1000 characters;
- one submission per `(student, offering)`.

## 7.6 Faculty — `/api/faculty/me`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/profile` | Faculty | Own profile |
| `GET` | `/dashboard` | Faculty | Ratings, distribution, insights |
| `GET` | `/comments` | Faculty | Anonymised comments |
| `GET` | `/trends` | Faculty | Trend series |
| `GET` | `/offerings` | Faculty | Own offerings |
| `GET` | `/filter-options` | Faculty | Available filters |
| `GET` | `/sentiment` | Faculty | Sentiment breakdown |
| `GET` | `/selections` | Faculty | Own teaching selections |
| `GET` | `/completion` | Faculty | Own subject completion counts and pending students |
| `POST` | `/selections` | Faculty | Add a selection |
| `PUT` | `/selections/{id}` | Faculty | Edit a selection |
| `DELETE` | `/selections/{id}` | Faculty | Deactivate a selection |
| `GET` | `/subject-requests` | Faculty | Own subject requests |
| `POST` | `/subject-requests` | Faculty | Request a new subject |

### `GET /faculty/me/completion`

Requires `subject_code`, `academic_year` (`YYYY-YY`) and `semester_number`. Faculty ownership comes from the JWT and an active selection; the endpoint never accepts a faculty ID. It returns aggregate counts, the feedback period and pending students only. There are no ratings, comments or feedback IDs. An empty verified roster returns `roster_available: false`; a scope the faculty member does not teach returns `404`.

### `POST /faculty/me/selections`

```json
{ "subject_code": "CS501", "academic_year": "2025-26", "semester_number": 5 }
```

Creating a selection also creates the matching `course_offerings` row if needed.

### `DELETE /faculty/me/selections/{id}`

Deactivates the selection. If the linked offering has no feedback it is removed; otherwise it is kept for history. Editing a selection that already has feedback returns `409`.

### `POST /faculty/me/subject-requests`

```json
{ "subject_code": "CS599", "subject_name": "Applied Deep Learning", "semester_number": 6 }
```

## 7.7 Administrator — `/api/admin`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/dashboard` | Admin | Department overview |
| `GET` | `/faculty` | Admin | List/search faculty |
| `POST` | `/faculty` | Admin | Create faculty account |
| `PATCH` | `/faculty/{id}/status` | Admin | Approve/reject/deactivate |
| `GET` | `/students` | Admin | List/search students |
| `POST` | `/students` | Admin | Create student |
| `PATCH` | `/students/{id}` | Admin | Edit student details |
| `PATCH` | `/students/{id}/status` | Admin | Activate/deactivate |
| `GET` | `/students/{id}` | Admin | Student submission metadata (no feedback text/ratings) |
| `GET` | `/enrollments` | Admin | Verified roster for one subject/year/semester |
| `POST` | `/enrollments` | Admin | Add one active student to a roster |
| `POST` | `/enrollments/bulk` | Admin | Add up to 500 USNs, reporting unknown/archived/duplicates |
| `DELETE` | `/enrollments/{id}` | Admin | Remove a roster row without touching feedback |
| `GET` | `/analytics/faculty/{id}` | Admin | Analytics for one faculty |
| `GET` | `/analytics/faculty-comparison` | Admin | Compare faculty |
| `GET` | `/subject-requests` | Admin | Pending/all requests |
| `PATCH` | `/subject-requests/{id}` | Admin | Approve or reject |
| `GET` | `/admins` | Admin | List administrators |
| `PATCH` | `/admins/{id}/status` | Admin | Activate/deactivate admin |
| `GET` | `/audit-logs` | Admin | Recent audit entries |

### `PATCH /admin/faculty/{id}/status`

```json
{ "status": "approved" }
```

Allowed values: `approved`, `rejected`, `inactive`.

### `PATCH /admin/subject-requests/{id}`

```json
{ "status": "approved", "admin_note": "Added to the semester 6 catalog." }
```

Approval adds the subject to `subjects`. It does **not** create a selection or offering for the requesting faculty member.

### Roster endpoints

All roster endpoints require `subject_code`, `academic_year` and `semester_number`. The subject must exist in the catalog and belong to that semester, the academic year must exist, and only active student accounts can be added. Adds are idempotent, are written to the audit log, and never create feedback. Removing a roster entry does not delete feedback already submitted by that student.

## 7.8 Analytics — `/api/analytics`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/faculty/me` | Faculty | Own analytics |
| `GET` | `/faculty/me/comparison` | Faculty | Own performance across their offerings |
| `GET` | `/admin` | Admin | Department analytics |
| `GET` | `/admin/faculty/{id}` | Admin | One faculty's analytics |
| `GET` | `/admin/faculty-comparison` | Admin | Department faculty comparison |

Common filters: `academic_year`, `semester_number`, `subject_code` (and `faculty_id` on `/admin`).

`GET /analytics/faculty/me/comparison` accepts only `subject_code`. `GET /analytics/admin/faculty-comparison` **requires** `subject_code` and also accepts `academic_year` and `semester_number`.

Analytics are computed from real feedback rows. See [14 — Analytics and AI](./14-analytics-and-ai.md) for the methodology.

## 7.9 AI / NLP — `/api/ml`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/model-info` | Any | Active engine and metadata |
| `POST` | `/sentiment` | Any | Classify up to 50 texts |
| `GET` | `/insights` | Faculty | Own insights bundle |

### `POST /ml/sentiment`

```json
{ "texts": [ { "text": "Very clear explanations." }, { "text": "The pace was too fast." } ] }
```

Response:

```json
{
  "method": "lexicon-v1",
  "results": [
    { "text": "Very clear explanations.", "label": "positive", "score": 0.6 },
    { "text": "The pace was too fast.", "label": "negative", "score": -0.4 }
  ]
}
```

Exact scores depend on the lexicon. The engine is deterministic and explainable.

## 7.10 Reports — `/api/reports`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/faculty/me` | Faculty | Own report (`format=csv` or `pdf`) |
| `GET` | `/faculty/me/completion` | Faculty | Pending-student PDF for one owned subject and period |
| `GET` | `/admin` | Admin | Department report (`format=csv` or `pdf`) |

Both performance reports return a file download with `Content-Disposition`. Filters: `academic_year`, `semester_number`, `subject_code`; the admin report also accepts `faculty_id`.

The completion report accepts only `format=pdf` plus the three scope parameters. It returns `409` when no verified roster exists and `404` when the faculty member does not teach the scope. Its pending table contains USN and name only; it never contains ratings, comments or internal feedback identifiers.

## 7.11 Error shapes

Validation error (`422`):

```json
{
  "detail": "Please check the submitted values.",
  "errors": [ { "field": "comment", "message": "String should have at least 10 characters" } ]
}
```

Generic error (`4xx`/`5xx`):

```json
{ "detail": "A human-readable message." }
```

Unexpected failures return a generic message; the stack trace is written to server logs only.

## 7.12 Related documents

- [08 — Authentication and Authorization](./08-authentication-and-authorization.md)
- [13 — Feedback Lifecycle](./13-feedback-lifecycle.md)
- [14 — Analytics and AI](./14-analytics-and-ai.md)

---

**Next:** [08 — Authentication and Authorization →](./08-authentication-and-authorization.md)
