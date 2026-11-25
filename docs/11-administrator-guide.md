# 11 — Administrator Guide

> **FacultyInsight AI** · Documentation set · [Back to index](../README.md#documentation-index)

This guide covers first-run setup and day-to-day administration.

## 11.1 First-run setup

The seed data creates **no user accounts**. The first administrator is created in the app.

1. Open the app and go to **`/setup`**.
2. Enter a name, email and a strong password.
3. Submit.

This calls `POST /api/auth/admin/setup`, which only succeeds while the `admins` table is empty. After the first admin exists, the page reports that setup is complete and the endpoint refuses further calls.

> Store the first administrator's credentials safely. There is no public "forgot password" flow; recovery is an operator-only CLI (see [11.9](#119-administrator-recovery)).

## 11.2 Sign in

1. Go to **`/login`** and choose the **Admin** tab.
2. Enter your email and password.

You land on **`/admin`**.

## 11.3 Dashboard (`/admin`)

| Section | What it shows |
|---------|---------------|
| Counts | Total students, faculty, subjects, responses |
| Performance by academic year | Average rating per year |
| Feedback responses by semester | Volume per semester |
| Faculty performance | Average rating per faculty member |
| Question-level averages | Department-wide average per question |
| Department improvement opportunities | Questions below the improvement threshold |

Filters: academic year, semester and subject. The dashboard is read-only.

## 11.4 Faculty management

Path: **`/admin/faculty`**.

### Create a faculty account

Provide name, email, department and a temporary password. The account can be created directly as approved, or left pending for the normal flow.

### Approve or reject

Faculty who self-register start as `pending`. Use the status action to set:

| Status | Effect |
|--------|--------|
| `approved` | Can sign in and be selected for offerings |
| `rejected` | Cannot sign in |
| `inactive` | Cannot sign in; kept for history |

### Notes

- Faculty choose their own subjects. Administrators do **not** assign teaching loads.
- Deactivating a faculty member does not delete their feedback history.

## 11.5 Student management

Path: **`/admin/students`**.

- **Create** a student with USN, name, department and password.
- **Edit** name and department.
- **Archive / restore** with the status toggle.
- **View submissions** — submission metadata only (counts and audit information), never feedback text or ratings.

Archiving blocks sign-in but keeps past feedback for aggregates. Students are not hard-deleted through the UI.

## 11.6 Catalog management

Path: **`/admin/catalog`**.

| Tab | Actions |
|-----|---------|
| Departments | Add, rename, delete (blocked if referenced) |
| Academic years | Add `YYYY-YY`, delete (blocked if referenced) |
| Subjects | Add, edit, delete (blocked if used by an offering) |
| Questions | Add, edit, activate/deactivate, delete (blocked if answered) |
| Periods | Create/update the date window per year + semester |

### Feedback periods

A period applies to **every offering** in that academic year and semester.

```text
academic_year = 2025-26
semester_number = 5
start_date = 2026-01-10
end_date   = 2026-01-25
```

- If no period exists, students see the offering as closed.
- `end_date` must be after `start_date`.
- Overlapping periods for the same year/semester are not possible (one row per pair).

### Questions

Only **active** questions appear on the form. Deactivating a question hides it from new submissions but keeps historical answers. Deleting a question that has answers returns `409`.

### Bootstrap

`POST /api/catalog/bootstrap` idempotently inserts the base department, academic years and default questions. It is useful after pointing the app at an empty database. It never overwrites user data.

## 11.7 Subject requests

Path: **`/admin/subject-requests`**.

Faculty can request subjects that are missing from the catalog. For each request you see the code, name, semester, requester and note.

| Action | Result |
|--------|--------|
| Approve | Subject is inserted into `subjects` (if not already present) |
| Reject | Request is marked rejected with your note |

Approval does **not** create a teaching selection or offering. The faculty member must still add the subject from their own page.

Only one **pending** request per subject code is allowed at a time.

## 11.8 Analytics and reports

- **Analytics** pages mirror the dashboard with per-faculty drill-down and comparison.
- **Reports**: choose CSV or PDF. The admin report covers the department and respects the current filters.

Reports never contain student identifiers.

## 11.9 Administrator recovery

If no administrator can sign in, use one of these operator-only paths. Neither is reachable from the public website.

### With database access

From `backend/`:

```powershell
python -m app.recover_admin --list
python -m app.recover_admin --email admin@college.edu --name "Administrator"
python -m app.recover_admin --email admin@college.edu --reset
```

`--reset` requires typing `RESET` and then a hidden new password.

### With an existing admin session

```powershell
python -m app.scripts.set_production_admin_password --email admin@college.edu
```

It talks to the public HTTPS API, never prints the password, and deletes the temporary recovery file after success.

## 11.10 Administrator accounts

Path: **`/admin/admins`**.

- List administrators and their status.
- Deactivate an administrator (for example when someone leaves).
- Create additional administrators with `POST /api/auth/admins`.

You cannot deactivate the account you are currently using through the UI.

## 11.11 Audit log

Path: **`/admin/audit`**.

The audit log records sensitive actions with actor role, actor id, action, entity, JSON details, IP address and timestamp. Examples:

- account creation and status changes;
- catalog create/update/delete;
- subject request review;
- feedback-related administrative actions.

Use it to answer "who changed this?" during a review.

## 11.12 Operational checklist

### Start of semester
1. Confirm academic year and semesters exist.
2. Confirm subjects for the semester are in the catalog.
3. Approve new faculty accounts.
4. Ask faculty to add their subject selections.
5. Create the feedback period.

### During feedback
1. Monitor response counts on the dashboard.
2. Handle subject requests promptly.
3. Do not edit questions mid-period unless necessary (it changes what students see).

### End of semester
1. Let the period close.
2. Export CSV/PDF reports.
3. Review improvement opportunities with faculty.
4. Deactivate accounts for anyone who has left.

## 11.13 Safety rules

- Never share administrator credentials.
- Never commit `.env` files or database dumps.
- Take a backup before any manual database change.
- Use the audit log when investigating a dispute.
- Rotate any credential that may have been exposed.

## 11.14 Related documents

- [06 — Migrations and Seeding](./06-migrations-and-seeding.md)
- [12 — Subject Selection and Requests](./12-subject-selection-and-requests.md)
- [15 — Security and Privacy](./15-security-and-privacy.md)
- [19 — Troubleshooting](./19-troubleshooting.md)

---

**Next:** [12 — Subject Selection and Requests →](./12-subject-selection-and-requests.md)
