# 15 — Security and Privacy

> **FacultyInsight AI** · Documentation set · [Back to index](../README.md#documentation-index)

This page describes the protections that are actually implemented. It separates what the code enforces from operational practices the operator must follow.

## 15.1 Threat model (practical)

| Threat | Mitigation |
|--------|-----------|
| Credential theft | bcrypt hashing; short-lived JWTs; rate-limited login |
| Privilege escalation | Server-side role guards on every protected route |
| Student identity leak | Reporting queries never select `student_id` |
| SQL injection | Parameterised queries everywhere |
| Cross-site request forgery | Bearer tokens in headers, not cookies |
| Cross-origin abuse | Explicit CORS allow-list |
| Brute force | In-process login rate limiter |
| Data loss | Additive migrations; backups; no destructive rollbacks |
| Secret leakage | `.env` ignored; placeholders in examples |
| Error-based information leak | Generic error bodies; details only in logs |

## 15.2 Authentication controls

- Passwords hashed with **bcrypt** (`bcrypt==5.0.0`), never stored or logged in plaintext.
- Password strength enforced server-side: minimum 8 characters, at least one letter and one number.
- JWT signed with **HS256**; secret from `JWT_SECRET_KEY`.
- Token lifetime **30 minutes** by default (`ACCESS_TOKEN_MINUTES`).
- Startup validation requires a secret of at least **16 characters** and rejects placeholders such as `change-me` in production.
- Account state is re-checked on every request, so deactivation takes effect immediately.

## 15.3 Authorization controls

- Role dependencies: `student_required`, `faculty_required`, `admin_required`.
- `faculty_id` and `student_id` always come from the token, never from the request body.
- Faculty dashboards, comments and reports are scoped to the caller.
- Admin-only routes are grouped under `/api/admin` and `/api/catalog` writes.
- The setup endpoint is available only while no administrator exists.

## 15.4 Input validation

- Pydantic models validate every request body:
  - USN pattern `^[A-Za-z0-9]{6,50}$`;
  - email format;
  - comment 10–1000 characters;
  - ratings 1–5;
  - semester 1–8;
  - academic year `YYYY-YY`.
- Database constraints duplicate the critical rules, so bad data cannot slip in through another path.
- Validation failures return `422` with field-level messages, not stack traces.

## 15.5 SQL safety

- All queries use psycopg parameter binding (`%s`), never string interpolation of user input.
- Dynamic filter clauses are built from a fixed allow-list of columns.
- Identifiers are never taken from user input.

## 15.6 Rate limiting

- Applies to student, faculty and admin login.
- Default: 12 attempts per 300 seconds (`LOGIN_RATE_LIMIT`, `LOGIN_RATE_WINDOW_SECONDS`).
- Exceeding the limit returns `429`.
- **Limitation:** the counter is per process and in memory. On serverless hosting it is per warm instance, not global. It slows brute force but is not a distributed defence.

## 15.7 Browser and transport security

`SecurityHeadersMiddleware` adds:

| Header | Value / purpose |
|--------|-----------------|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` (clickjacking) |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | Disables camera, microphone and geolocation |
| `Cache-Control` | `no-store` by default |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` (production only) |
| `X-Request-ID` | Request correlation |

CORS:

- explicit origin allow-list from `CORS_ORIGINS`;
- `allow_credentials=False` (no cookies);
- limited methods and headers.

Production:

- HTTPS terminated by Vercel;
- `/docs`, `/redoc` and `/openapi.json` disabled when `APP_ENV=production`.

## 15.8 Error handling

- `psycopg.OperationalError` → `503` with a friendly message.
- Any unhandled exception → `500` with a generic message.
- Stack traces and database details go to server logs only.
- Request IDs let an operator correlate a user report with a log line.

## 15.9 Audit logging

`audit_logs` records:

| Field | Content |
|-------|---------|
| `actor_role`, `actor_id` | Who did it |
| `action` | What happened (for example `faculty.status.update`) |
| `entity_type`, `entity_id` | What it affected |
| `details` | JSON context |
| `ip_address` | Client IP |
| `created_at` | Timestamp |

Audited actions include account creation and status changes, catalog changes, subject-request review and other administrative writes.

Audit rows are written inside the same transaction as the action where possible, so a failed action does not leave a misleading log.

## 15.10 Privacy and data minimisation

### What is stored

| Data | Why |
|------|-----|
| Student USN, name, department, password hash | Account and access |
| Faculty name, email, department, password hash | Account and access |
| Admin name, email, password hash | Account and access |
| Feedback ratings and comment | The product's purpose |
| `feedback.student_id` | Enforce one submission per offering |
| Audit entries | Accountability |

### What is not stored

- No phone numbers, addresses, dates of birth or photos.
- No IP-based tracking beyond the audit log.
- No third-party analytics or advertising scripts.
- No plaintext passwords.

### Anonymity guarantees

- Faculty and admin analytics queries never select `feedback.student_id`.
- Comment endpoints return text only.
- Reports exclude student identifiers.
- The student ID link exists only inside the database row for uniqueness.

### Residual risk

In a very small class, a distinctive comment could be recognisable. This is inherent to free-text feedback and is documented in [20 — Known Limitations](./20-known-limitations.md).

## 15.11 Secret management

Rules for operators and contributors:

1. Never commit `.env`, `.env.local` or any file containing real credentials.
2. Use `.env.example` templates with placeholders only.
3. Keep `DATABASE_URL`, `JWT_SECRET_KEY` and database passwords out of issues, screenshots and chat.
4. Rotate any secret that may have been exposed.
5. Do not commit database dumps; `database/backups/` is git-ignored.
6. Do not commit temporary admin-recovery files (for example `~/.facultyinsight-admin-recovery.txt`).

The `.gitignore` is configured to exclude `.env`, build output, backups and local test helpers.

## 15.12 Administrator recovery safety

- Recovery is a CLI that requires direct database access or an existing admin session.
- It is not exposed through the public website.
- It never prints passwords or hashes.
- Password resets require explicit confirmation.
- The HTTPS-based script deletes its temporary recovery file after success.

## 15.13 Backups and retention

- Take a `pg_dump` before any manual schema or data change.
- Store backups outside the repository.
- Restrict access to backups: they contain personal data.
- Define a retention period appropriate to your institution's policy.
- Test a restore at least once per academic cycle.

```powershell
pg_dump -U postgres -d faculty_feedback -Fc -f database/backups/manual_$(Get-Date -Format yyyyMMdd_HHmmss).dump
```

## 15.14 Deployment hardening checklist

- [ ] `APP_ENV=production`
- [ ] Strong, unique `JWT_SECRET_KEY` (32+ random characters)
- [ ] Database password rotated and stored only in the host's secret manager
- [ ] `CORS_ORIGINS` lists only real frontend origins
- [ ] HTTPS enforced
- [ ] `/docs` and `/openapi.json` unreachable in production
- [ ] First admin created and recovery file deleted
- [ ] Backups scheduled and tested
- [ ] No `.env` or dump committed to Git
- [ ] Dependencies reviewed for known vulnerabilities

## 15.15 Reporting a security issue

Do not open a public issue containing exploit details or personal data. Contact the maintainer privately, include reproduction steps with secrets redacted, and allow time for a fix before disclosure.

## 15.16 Related documents

- [08 — Authentication and Authorization](./08-authentication-and-authorization.md)
- [17 — Deployment](./17-deployment.md)
- [19 — Troubleshooting](./19-troubleshooting.md)
- [20 — Known Limitations](./20-known-limitations.md)

---

**Next:** [16 — Installation on Windows →](./16-installation-on-windows.md)
