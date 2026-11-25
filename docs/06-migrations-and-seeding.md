# 06 — Migrations and Seeding

> **FacultyInsight AI** · Documentation set · [Back to index](../README.md#documentation-index)

This page explains how the database is created, seeded and upgraded. All migrations are **additive**: they create or alter, never drop or truncate user data.

## 6.1 Files

| File | Purpose |
|------|---------|
| `database/schema.sql` | Creates the canonical 15-table schema |
| `database/seed.sql` | Inserts reference data (no user accounts) |
| `database/migrations/001_additive_upgrade.sql` | Adds columns/constraints to a legacy database |
| `database/migrations/002_faculty_subject_selections.sql` | Adds selections and subject requests |
| `database/migrations/003_deactivate_backfilled_selections.sql` | Corrects selections backfilled by an earlier revision |
| `backend/app/schema.py` | Re-applies the additive changes at runtime, with an advisory lock |

## 6.2 Creating a fresh database

From a PostgreSQL shell:

```sql
CREATE DATABASE faculty_feedback;
```

Then load the schema and seed data:

```powershell
psql -U postgres -d faculty_feedback -f database/schema.sql
psql -U postgres -d faculty_feedback -f database/seed.sql
```

Or, if you use Docker Compose, the database service mounts these files and runs them automatically on first start (see [17 — Deployment](./17-deployment.md)).

## 6.3 What `seed.sql` inserts

`seed.sql` is **reference data only**. It creates:

| Table | Rows |
|-------|------|
| `departments` | 1 — `Computer Science and Engineering` (`CSE`) |
| `semesters` | 8 — 1 through 8 |
| `academic_years` | 4 — `2025-26`, `2026-27`, `2027-28`, `2028-29` |
| `feedback_questions` | 5 default questions |
| `subjects` | 54 CSE subjects across semesters 1–7 |

Important facts:

- **`seed.sql` creates no user accounts.** There is no default admin, faculty or student.
- **Semester 8 has no subjects** because it is internship-only.
- Inserts are idempotent (`ON CONFLICT DO NOTHING` / `WHERE NOT EXISTS`), so re-running the file is safe.
- The catalog endpoints can also bootstrap missing base data at runtime (see `POST /catalog/bootstrap`).

The five default questions are:

1. Explains concepts clearly.
2. Has good subject knowledge.
3. Encourages student participation.
4. Uses practical examples.
5. Completes the syllabus.

## 6.4 Creating the first administrator

Because the seed creates no users, the first administrator is created through the **setup screen**:

1. Open the app (for example `http://localhost:5173`).
2. Go to `/setup`.
3. Enter name, email and password.

The endpoint behind it is `POST /api/auth/admin/setup`. It succeeds only while **no administrator exists**. After that, the setup page reports that setup is complete and the endpoint refuses further calls.

`GET /api/auth/setup-status` tells the frontend whether setup is still available.

> Keep the first administrator's credentials safe. Recovery is an operator-only CLI (see [8.9 Administrator recovery](./08-authentication-and-authorization.md#89-administrator-recovery)).

## 6.5 Migration 001 — additive upgrade

For databases created by an older version of the project. It adds:

- `faculty.created_at`, `students.created_at`, `admins.created_at`, `course_offerings.created_at`;
- `admins.is_active`;
- `feedback.updated_at`, plus a default for `feedback.submitted_at`;
- missing check/unique/foreign-key constraints, validating legacy `NOT VALID` constraints;
- the `audit_logs` table if it does not exist;
- the indexes used by the current code.

It backfills `NULL` values before setting `NOT NULL`, and it does not delete anything.

## 6.6 Migrations 002 and 003 — teaching selections

### 002 — `faculty_subject_selections.sql`

Creates:

- `faculty_subject_selections`
- `subject_requests`
- supporting indexes

It deliberately does **not** create selections for existing offerings. Faculty must choose their own subjects.

> An earlier revision of this migration copied every existing offering into a selection. Migration 003 corrects that.

### 003 — `deactivate_backfilled_selections.sql`

Identifies rows created by the automatic backfill and sets `is_active = FALSE`:

- they share the earliest selection timestamp (the backfill transaction);
- they were never edited (`updated_at IS NULL`);
- their offering existed before the selection was inserted.

An explicit faculty selection creates or reuses its offering in the same transaction, so it is left untouched. Offerings and feedback are preserved. The migration records itself in `schema_migrations`.

## 6.7 Runtime schema upgrades

`backend/app/schema.py` exists because production database credentials belong to the hosting platform. On the first database-backed request of each process it:

1. Takes a transaction-scoped advisory lock.
2. Checks which required tables/columns/indexes exist.
3. Creates only what is missing.
4. Applies the data corrections for backfilled selections.
5. Inserts the applied version into `schema_migrations` so each correction runs at most once.
6. Commits and releases the lock.

Guarantees, copied from the module docstring:

- only creates missing tables, columns and indexes;
- never drops or truncates a table, column or row;
- never assigns subjects to faculty automatically;
- deactivates rows that an earlier migration backfilled, while keeping offerings and feedback intact;
- adds the reversible student archive flag without changing existing accounts;
- records applied corrections so each runs at most once;
- serialises concurrent cold starts with an advisory lock.

Because of this, a fresh production database only needs `schema.sql` and `seed.sql`; the runtime upgrade handles the rest on first use.

## 6.8 Applying migrations manually

For an existing database, run the files in order:

```powershell
psql -U postgres -d faculty_feedback -f database/migrations/001_additive_upgrade.sql
psql -U postgres -d faculty_feedback -f database/migrations/002_faculty_subject_selections.sql
psql -U postgres -d faculty_feedback -f database/migrations/003_deactivate_backfilled_selections.sql
```

Each file wraps its work in `BEGIN; … COMMIT;` and is idempotent.

## 6.9 Test database

The backend tests use a dedicated database, `faculty_feedback_test` by default. The test fixture:

- creates the schema once per session from `database/schema.sql`;
- truncates and reseeds between tests;
- never touches development or production data.

Set it explicitly if needed:

```powershell
$env:TEST_DB_NAME = "faculty_feedback_test"
```

See [18 — Testing](./18-testing.md) for the full command and the important `DATABASE_URL` caveat.

## 6.10 Rollback policy

There are **no destructive down-migrations**. The design is forward-only:

- To undo a schema change, write a new additive migration.
- To remove an account, deactivate it (`is_active` / `status`).
- To remove a teaching selection, deactivate it so feedback history is preserved.
- To remove a catalog item, delete it only if nothing references it; otherwise the API returns `409`.

Before any manual production change, take a backup:

```powershell
pg_dump -U postgres -d faculty_feedback -Fc -f database/backups/manual_$(Get-Date -Format yyyyMMdd_HHmmss).dump
```

`database/backups/` is git-ignored. Never commit dumps — they can contain personal data.

## 6.11 Related documents

- [05 — Database Schema](./05-database-schema.md)
- [11 — Administrator Guide](./11-administrator-guide.md)
- [16 — Installation on Windows](./16-installation-on-windows.md)
- [17 — Deployment](./17-deployment.md)

---

**Next:** [07 — API Reference →](./07-api-reference.md)
