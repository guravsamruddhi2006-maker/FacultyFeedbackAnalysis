# 08 — Authentication and Authorization

> **FacultyInsight AI** · Documentation set · [Back to index](../README.md#documentation-index)

## 8.1 Model

FacultyInsight AI uses **stateless JWT authentication** with **role-based access control (RBAC)**.

```text
Login ──► verify password (bcrypt) ──► issue JWT (HS256, 30 min)
                                          │
Request ──► decode JWT ──► load account row ──► role guard ──► route
```

There are no server-side sessions and no refresh tokens. The token is the session.

## 8.2 Account types

| Role | Identifier | Table | Active flag |
|------|-----------|-------|-------------|
| Student | USN | `students` | `is_active` |
| Faculty | Email | `faculty` | `status = 'approved'` |
| Administrator | Email | `admins` | `is_active` |

### Faculty status

| Status | Can sign in? | Can be selected for offerings? |
|--------|--------------|-------------------------------|
| `pending` | No | No |
| `approved` | Yes | Yes |
| `rejected` | No | No |
| `inactive` | No | No |

A faculty member registers themselves; an administrator must approve the account before it becomes usable.

### Student and admin flags

`is_active = FALSE` blocks sign-in. Deactivation is reversible and does not delete feedback history.

## 8.3 Password handling

- Passwords are hashed with **bcrypt** (`bcrypt==5.0.0`). Plaintext is never stored or logged.
- Password rules (enforced server-side and mirrored in the frontend):
  - at least 8 characters;
  - at least one letter;
  - at least one number.
- `hash_password` validates strength before hashing.
- `verify_password` returns `False` for missing or malformed hashes rather than raising.

## 8.4 JWT details

| Property | Value |
|----------|-------|
| Algorithm | `HS256` |
| Secret | `JWT_SECRET_KEY` environment variable |
| Lifetime | `ACCESS_TOKEN_MINUTES` (default `30`) |
| Claims | `sub` (account id), `role`, `iat`, `exp` |

At startup, `settings.validate()` enforces:

- `JWT_SECRET_KEY` is at least **16 characters**;
- in production (`APP_ENV=production`), the secret must not be a placeholder such as `change-me`.

The frontend stores the token in `localStorage` under `facultyinsight.token`. On a `401` it clears the token and returns the user to `/login`.

## 8.5 Role guards

`backend/app/core/deps.py` defines:

| Dependency | Allows |
|------------|--------|
| `get_current_user` | Any valid, active account |
| `authenticated` | Any signed-in role |
| `student_required` | Students only |
| `faculty_required` | Approved faculty only |
| `admin_required` | Active administrators only |

`get_current_user` does not trust the token alone. After decoding it, it re-reads the account row to confirm the account still exists and is active/approved. This means deactivating an account takes effect on the **next request**, even if the token has not expired.

## 8.6 Login rate limiting

`login_rate_limiter` is an in-process limiter applied to all three login endpoints.

| Setting | Default | Meaning |
|---------|---------|---------|
| `LOGIN_RATE_LIMIT` | `12` | Attempts allowed per window |
| `LOGIN_RATE_WINDOW_SECONDS` | `300` | Window length in seconds |

When the limit is exceeded the endpoint returns `429`.

> **Important:** the limiter is per process and in memory. On Vercel, each serverless instance has its own counter, so the effective limit is per warm instance, not global. It is a brute-force speed bump, not a distributed defence. See [20 — Known Limitations](./20-known-limitations.md).

## 8.7 Authorization rules by area

| Area | Rule |
|------|------|
| Student endpoints | A student can only read/write their own feedback. `student_id` is always taken from the token, never from the request body. |
| Faculty endpoints | A faculty member can only read their own dashboard, comments, selections and reports. `faculty_id` is taken from the token. |
| Admin endpoints | Require an active administrator. |
| Analytics | Faculty see only their own data; administrators see aggregates. |
| Reports | `GET /reports/faculty/me` is scoped to the caller; `GET /reports/admin` requires admin. |
| Catalog writes | Administrators only. Reads require a signed-in user (except public departments). |
| Setup | Only works while no administrator exists. |

### Why a student cannot see another student's feedback

- `FeedbackSubmit` has no `student_id` field by design.
- Every student query is parameterised with `current_user.id`.
- Faculty and analytics queries never select `feedback.student_id`.

## 8.8 Account lifecycle

### Student
1. Register at `/register/student`.
2. Sign in.
3. Administrator can edit details or deactivate.
4. Deactivated students cannot sign in; their past feedback remains for aggregate reporting.

### Faculty
1. Register at `/register/faculty` → `pending`.
2. Administrator approves → `approved`.
3. Faculty selects subjects and appears to students.
4. Administrator can set `rejected` or `inactive`.

### Administrator
1. First admin created at `/setup`.
2. Additional admins created by an existing admin (`POST /api/auth/admins`).
3. Admins can be deactivated but not deleted through the UI.

## 8.9 Administrator recovery

If nobody can sign in as an administrator, there are two operator-only paths.

### Path A — database access (CLI)

From `backend/`:

```powershell
python -m app.recover_admin --list
python -m app.recover_admin --email admin@college.edu --name "Administrator"
python -m app.recover_admin --email admin@college.edu --reset
```

`--reset` asks for an explicit `RESET` confirmation and a hidden new password. The command never prints a password or hash.

### Path B — existing admin session (HTTPS only)

`backend/app/scripts/set_production_admin_password.py` changes a password through the public API. It reads the current password from a hidden prompt (or a temporary recovery file), prompts for the new password with `getpass`, and deletes the temporary recovery file after success.

```powershell
python -m app.scripts.set_production_admin_password --email admin@college.edu
```

Both paths are documented in [19 — Troubleshooting](./19-troubleshooting.md).

## 8.10 Transport and browser security

- HTTPS is provided by Vercel in production.
- Security headers include `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` and, in production, `Strict-Transport-Security`.
- CORS uses an explicit allow-list (`CORS_ORIGINS`), not `*`.
- `allow_credentials` is `False` because the API uses bearer tokens, not cookies.

See [15 — Security and Privacy](./15-security-and-privacy.md) for the full list.

## 8.11 Related documents

- [07 — API Reference](./07-api-reference.md)
- [15 — Security and Privacy](./15-security-and-privacy.md)
- [19 — Troubleshooting](./19-troubleshooting.md)

---

**Next:** [09 — Student Guide →](./09-student-guide.md)
