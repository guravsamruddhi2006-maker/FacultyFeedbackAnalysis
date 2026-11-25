# FacultyInsight AI — Security and Privacy

## 1. Password handling

- bcrypt hashing (`bcrypt.hashpw` / `checkpw`).
- Strength policy: minimum 8 characters, at least one letter and one number, max 72 bytes.

## 2. Authentication

- JWT HS256 bearer tokens with `sub`, `role`, `iat`, `exp`.
- Short-lived access tokens (default 30 minutes).
- Login rate limiting per client IP and path.

## 3. Authorisation

- Backend role dependencies enforce `admin`, `faculty`, `student` per endpoint.
- There is no public administrator registration. The first administrator is created once through the initial setup; later administrators are created by an authenticated administrator.
- Administrator and faculty identities live in separate tables with separate login endpoints. The same email can therefore be an administrator and a pending faculty registration without either role being changed silently.
- Only administrators can approve, reject or deactivate faculty accounts.
- Only administrators can archive or restore student accounts. Archiving keeps the row, historical feedback and audit logs, but rejects new logins and invalidates already-issued tokens on their next request.
- Operator recovery never reopens public registration. Database-level recovery is available through `app.recover_admin`; when database credentials are unavailable, an existing administrator can change a password through the hidden-prompt `app.scripts.set_production_admin_password` tool.
- Faculty data scope is derived from the JWT subject; request input cannot widen scope.
- Students can only access their own feedback records.
- Faculty can only view their own aggregated feedback.
- Admins are restricted to administrative actions.

## 4. Privacy

- Faculty and admin analytics return aggregates only.
- Faculty comments include sentiment and topic metadata, never student identity.
- Reports exclude student names, USNs and emails; they include aggregated numbers and anonymised comments.
- Admin student submission views intentionally exclude feedback text/ratings.

## 5. Transport and headers

- CORS allow-list from environment.
- Security headers: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy`, `Cache-Control: no-store`, HSTS in production.
- Interactive API docs (`/docs`, `/redoc`) and OpenAPI schema (`/openapi.json`) are disabled when `APP_ENV=production`.

## 6. Data protection

- Parameterised SQL only (psycopg `%s` placeholders; no string interpolation into SQL text).
- Pydantic validation on all request bodies.
- Generic server errors; internal details logged server-side only.
- Secrets via environment variables; `.env` files excluded from version control.

## 7. Audit

- Administrative actions write audit log entries with actor role/id, action, entity type/id, JSON details, IP.

## 8. Known limitations

- Login limiter is per-process; production multi-worker deployments should use Redis or gateway-level limiting.
- JWT is stateless; no server-side token revocation (short expiry mitigates).
