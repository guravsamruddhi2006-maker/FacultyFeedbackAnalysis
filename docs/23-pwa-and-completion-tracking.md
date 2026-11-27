# 23 — PWA, responsive UI and completion tracking

This document records the PWA, interface refresh, faculty completion tracker,
pending-student PDF export and WhatsApp reminder work. It is both an operator
guide and the completion report for that change.

Status: implemented and verified locally. **Nothing was deployed to production**
and no production data was changed.

---

## 1. What changed

| Area | Change |
|------|--------|
| PWA | Web app manifest, PNG/maskable/apple icons, service worker, offline page, install prompt, update prompt |
| UI | Navy/teal academic palette, display serif headings, responsive shell, accessible focus states and reduced-motion support |
| Faculty | Completion tracker at `/faculty/completion` for the faculty member's own subjects and periods |
| Administrator | Verified class rosters at `/admin/rosters` for adding/removing eligible students |
| Reporting | Pending-student PDF at `GET /api/reports/faculty/me/completion` |
| Reminders | User-triggered WhatsApp share/copy with aggregate counts only |
| Data | Additive `student_enrollments` table and `004_student_enrollments.sql` migration |
| Tests | Completion/roster/PDF backend tests, WhatsApp and PWA unit tests, responsive Playwright checks |

The application remains one React SPA on top of the existing FastAPI API and
PostgreSQL database. No second app, stack change or native client was added.

---

## 2. PWA behaviour

### Manifest and icons

- `frontend/public/manifest.webmanifest`
  - `name`: FacultyInsight AI
  - `short_name`: FacultyInsight
  - `start_url` and `scope`: `/`
  - `display`: `standalone` (with `display_override`)
  - theme and background: `#0b1f3a`
  - 192×192, 512×512 and maskable 512×512 icons
  - shortcuts for the workspace and sign-in
- `frontend/public/icons/` contains the generated PNG icons and the Apple touch
  icon. They are committed, so production builds do not need Pillow.
- `frontend/scripts/generate_pwa_icons.py` regenerates the icons if the brand
  mark changes. It is a development utility only.
- `frontend/index.html` links the manifest, favicon, Apple touch icon and
  install-related meta tags. `frontend/public/favicon.svg` was refreshed to the
  navy/teal mark.

This is an **installable web app**. It is not an Android APK, an iOS app or an
App Store/Play Store listing, and the interface says so explicitly.

### Service worker

`frontend/public/sw.js` uses a small, explicit strategy:

| Request | Strategy |
|---------|----------|
| `/api/*` | Never intercepted; always live |
| Navigations | Network first, cached page fallback, then `/offline.html` |
| Hashed assets, icons, manifest | Cache first with background refresh |
| `sw.js` itself | Never cached by the worker |

- `install` pre-caches the app shell and tolerates a missing optional asset.
- `activate` removes caches from older versions and claims open clients.
- The worker does **not** call `skipWaiting` on install, so an open tab is not
  reloaded under the user.
- A waiting worker is announced through `facultyinsight:sw-update`; the UI asks
  the user before reloading.

### Install and update UI

- `frontend/src/lib/pwa.ts` detects standalone mode, iOS/iPadOS, and Safari,
  registers the worker and applies updates.
- `frontend/src/components/PwaManager.tsx` captures `beforeinstallprompt`,
  shows a dismissible install card, and provides iOS “Add to Home Screen”
  instructions. Dismissal is remembered in `localStorage` under
  `facultyinsight.install-dismissed`.
- The sidebar has an **Install app** entry that triggers the browser prompt when
  available and otherwise opens the same instructions. It is hidden when the app
  is already standalone.
- When a new worker is waiting, a “A new version is ready” card lets the user
  reload now or later.
- Registration is best-effort. If service workers are unavailable, the normal
  web app continues to work.

### Offline behaviour

`frontend/public/offline.html` is a branded, dependency-free fallback. It states
that feedback, rosters and reports need a live connection and that work is never
queued while offline. The app shell may open offline; **no feedback is submitted,
queued or cached for later submission**.

---

## 3. Interface and responsive design

- Tokens live in `frontend/src/index.css`: navy primary, teal accent/ring,
  neutral surfaces, destructive red and a shared radius.
- Headings use a display serif; body text stays Inter for readability.
- `tailwind.config.js` adds the display font family and an `academic` shadow.
- `frontend/src/components/ui.tsx` uses the new primary hover, teal info badges
  and teal accents. Buttons, tables, alerts, modals, inputs and empty states keep
  their existing APIs, so current screens were not rewritten.
- Focus-visible outlines use the teal ring; `prefers-reduced-motion` removes
  animation and smooth scrolling.
- The authenticated shell scrolls its navigation independently, so eight admin
  links and the account footer remain reachable on short screens.
- Content is constrained to `max-w-7xl`, with responsive padding and grid
  breakpoints; tables scroll horizontally instead of forcing page overflow.
- The sign-in page was exercised at **320, 375, 430, 768, 1366 and 1920 px** with
  no horizontal page overflow.

---

## 4. Faculty completion tracker

### Why a roster table was required

There was no student-to-subject roster. Treating every registered student as
eligible would fabricate a class list and produce false percentages. Completion
therefore uses a new administrator-maintained table:

```sql
student_enrollments(
  enrollment_id,
  student_id,
  subject_code,
  academic_year,
  semester_number,
  created_at
)
```

`UNIQUE (student_id, subject_code, academic_year, semester_number)` makes roster
adds idempotent. Indexes cover scope lookups and per-student lookups. The table is
additive: no existing row, column or table is dropped or rewritten.

### Eligibility rules

- Only rows in `student_enrollments` for the exact subject, academic year and
  semester count.
- Archived (`is_active = FALSE`) students are excluded from counts and pending
  lists.
- The subject must exist in the catalog and belong to the selected semester.
- The academic year must exist.
- Faculty ownership is enforced by an **active** `faculty_subject_selections`
  row for the authenticated faculty member and the same scope.
- Submitted means the student appears in feedback for **that faculty member's**
  offering in the scope. Another faculty member teaching the same subject cannot
  change the result.
- Registered students outside the roster are ignored.
- With an empty roster the API returns `roster_available: false`, zero counts and
  an empty pending list. It never guesses.

### Privacy model

Completion status and anonymous feedback stay separate:

- The response contains counts, percentage, period metadata and pending
  `student_id`/`name` only.
- It contains no ratings, comments, sentiment, feedback IDs or offering IDs.
- Faculty and admin analytics/report queries still never return student IDs for
  submitted feedback.
- The PDF contains no feedback content and no internal identifiers.
- The WhatsApp reminder contains aggregate counts only — no student names, USNs,
  phone numbers, ratings or comments.
- The submitted student is never named in the completion response; the pending
  list is the only identity-bearing part, and it is limited to students who have
  not submitted.

The tracker explains this in-product and links the lack of a roster to the
administrator roster screen.

### Faculty API

`GET /api/faculty/me/completion` (`faculty` only)

Query parameters:

| Name | Rule |
|------|------|
| `subject_code` | 2–20 characters; normalised to uppercase |
| `academic_year` | `YYYY-YY`, for example `2026-27` |
| `semester_number` | 1–8 |

Response (abridged):

```json
{
  "subject_code": "CS501",
  "subject_name": "Data Structures",
  "academic_year": "2026-27",
  "semester_number": 5,
  "period": { "start_date": "...", "end_date": "...", "is_open": true },
  "roster_available": true,
  "eligible_count": 40,
  "submitted_count": 27,
  "pending_count": 13,
  "completion_percentage": 67.5,
  "pending_students": [{ "student_id": "4UB26CS002", "name": "..." }],
  "privacy_notice": "...",
  "methodology": "..."
}
```

Errors:

- `404` — the faculty member has no active selection for that scope.
- `401/403` — unauthenticated, pending faculty or wrong role.

### Administrator roster API

All routes require an administrator.

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/admin/enrollments?subject_code=&academic_year=&semester_number=` | List the verified roster |
| `POST` | `/api/admin/enrollments` | Add one USN (idempotent) |
| `POST` | `/api/admin/enrollments/bulk` | Add up to 500 USNs, reporting unknown/archived/duplicate entries |
| `DELETE` | `/api/admin/enrollments/{enrollment_id}` | Remove one roster row without touching feedback |

Adds validate the catalog scope and require an existing, active student.
Sensitive changes write audit events (`student_enrollment.add`,
`student_enrollment.bulk_add`, `student_enrollment.remove`). Removing a roster
row never deletes feedback.

---

## 5. Pending-student PDF

`GET /api/reports/faculty/me/completion?format=pdf&subject_code=...&academic_year=...&semester_number=...`

- Faculty only; scope ownership is enforced exactly like the JSON endpoint.
- Returns `409` when the verified roster is empty or absent, with an explanation
  that an administrator must add the class.
- Returns `404` when the faculty member does not teach the scope.
- The PDF contains:
  - institution/product heading
  - faculty, subject, academic year and semester
  - feedback-period dates and open/closed status
  - generated timestamp
  - eligible, submitted, pending and completion-percentage summary
  - pending USN and student name table
  - privacy, methodology and scope notes
- It contains **no ratings, comments, sentiment results, feedback IDs or other
  internal identifiers**.
- The filename is `feedback-completion-<subject>-<year>-sem-<n>-<timestamp>.pdf`.

The existing `downloadReport` helper appends `format=pdf`; the route accepts only
`pdf`.

---

## 6. WhatsApp reminder

`frontend/src/lib/whatsapp.ts` builds the message and link.

- The user clicks **Share reminder on WhatsApp**; a `wa.me/?text=` URL opens in a
  new tab with a prefilled message. Nothing is sent automatically.
- **Copy reminder** provides the same text for class groups or other channels.
- The message contains subject, year, semester, aggregate submitted/eligible
  counts and the remaining count. When everyone has submitted it says so.
- It explicitly states that responses are anonymous and faculty never see who
  submitted which rating or comment.
- It never asks for or uses phone numbers, never scrapes contacts and never
  exposes student identities.
- The pending list is shared only by manually attaching the downloaded PDF.

---

## 7. Database migration

Files:

- `database/schema.sql` — canonical schema now includes `student_enrollments`.
- `database/migrations/004_student_enrollments.sql` — additive, idempotent
  migration, records `004_student_enrollment_roster` in `schema_migrations`.
- `backend/app/schema.py` — runtime upgrade for existing deployments, guarded by
  an advisory lock and the same migration version.

Upgrade behaviour:

1. Deploy the new code.
2. The first database-backed request applies the runtime upgrade if needed.
3. Existing data is untouched; the table starts empty.
4. Faculty completion stays explicitly unavailable until an administrator adds
   students to a roster.
5. Optionally run the SQL migration manually in environments that do not rely on
   runtime upgrades.

No environment variables were added or changed. Rollback can leave the empty
table in place; dropping it is not required for the rest of the app to work.

---

## 8. Tests and verification

Commands were run from the repository root (PowerShell).

### Backend

```powershell
$env:DATABASE_URL = "postgresql://postgres:<local-password>@localhost:5432/faculty_feedback"
$env:TEST_DB_NAME = "faculty_feedback_test"
.\.venv\Scripts\python.exe -m pytest backend\tests -q
```

Result: **86 passed** (77 pre-existing + 9 new completion/roster/PDF tests).

New coverage in `backend/tests/test_completion.py`:

- no roster → explicit `roster_available: false`, zero counts
- roster counts, percentage and pending list
- feedback from a non-roster student is ignored
- submitted student ID, comments and feedback IDs are absent from the response
- faculty B cannot read faculty A's scope (404), and can read their own subject
- students receive 403
- PDF without a roster returns 409; with a roster returns a real PDF attachment
- administrator single/bulk add, duplicate idempotency, removal and audit log
- archived students are rejected
- subject/semester scope mismatch is rejected

`backend/tests/conftest.py` now truncates `student_enrollments` between tests.

### Frontend

```powershell
cd frontend
npm test
npm run build
```

- Vitest: **21 passed** across 6 files.
  - WhatsApp message privacy and `wa.me` encoding
  - PWA manifest/icon/service-worker/offline-shell integrity
  - completion page counts, pending-only list and unavailable-roster state
  - existing password, protected-route and auth tests
- `tsc --noEmit && vite build`: passed.
- Playwright (`npx playwright test e2e/pwa.spec.ts`): **8 passed**.
  - manifest and touch icon reachable, icons valid
  - offline page served
  - sign-in page at 320/375/430/768/1366/1920 px with no horizontal overflow
  - primary controls visible at every width

The existing Playwright auth/deep specs were not rerun in this pass; they require
the backend on the isolated test database and mutate shared fixture rows. No
existing API contract or route used by those specs was removed.

### Browser/product checks still requiring manual review

- Real Chrome/Edge install prompt on HTTPS or localhost
- iOS Safari “Add to Home Screen” flow on a physical device
- Screen-reader pass over the new roster and completion screens
- Lighthouse PWA/accessibility audit against a deployed build

These are verification steps, not unresolved code work.

---

## 9. Files added or changed

### Database

- `database/schema.sql`
- `database/migrations/004_student_enrollments.sql`

### Backend

- `backend/app/schema.py`
- `backend/app/schemas/completion.py`
- `backend/app/services/completion_service.py`
- `backend/app/services/report_service.py`
- `backend/app/api/admin.py`
- `backend/app/api/faculty.py`
- `backend/app/api/reports.py`
- `backend/tests/conftest.py`
- `backend/tests/test_completion.py`

### Frontend

- `frontend/index.html`
- `frontend/tailwind.config.js`
- `frontend/public/{manifest.webmanifest,sw.js,offline.html,favicon.svg}`
- `frontend/public/icons/*`
- `frontend/scripts/generate_pwa_icons.py` (development utility)
- `frontend/src/index.css`
- `frontend/src/main.tsx`
- `frontend/src/App.tsx`
- `frontend/src/components/{Layout,PwaManager,ui}.tsx`
- `frontend/src/lib/{pwa,whatsapp,types}.ts`
- `frontend/src/pages/faculty/FacultyCompletion.tsx`
- `frontend/src/pages/admin/AdminRosters.tsx`
- `frontend/src/lib/{pwa,whatsapp}.test.ts`
- `frontend/src/pages/faculty/FacultyCompletion.test.tsx`
- `frontend/e2e/pwa.spec.ts`

---

## 10. Deliberate limits

- There is no ERP/college-system import. Rosters are entered by an administrator
  (one at a time or pasted USN list). A CSV upload would be a reasonable next
  step but was not added without a verified source format.
- Small classes still carry inherent anonymity risk. A pending list plus a single
  submission can narrow participation; the product states this and keeps
  feedback content separate.
- The service worker caches the shell, not data. There is no offline submission,
  background sync or push notification.
- WhatsApp is a share action, not an integration. The PDF must be attached
  manually, and no phone number is collected or exposed.
- PWA installation availability depends on the browser, HTTPS and its install
  criteria; the UI never claims universal support.
- The PDF is generated in memory, so very large rosters are still subject to the
  existing serverless time/memory limits.

---

## 11. Requirement checklist

| Requirement | Status |
|-------------|--------|
| Preserve existing student/faculty/admin workflows | Yes — additive routes, optional UI entries, no removed APIs |
| PWA manifest, icons, service worker, standalone mode | Yes |
| Install prompts where supported; iOS instructions | Yes |
| Offline fallback and update handling | Yes |
| Never claim native APK/App Store app | Yes — install UI says it is a web app |
| Navy/teal academic palette and reusable tokens | Yes |
| WCAG 2.2 AA target, responsive at 320–1920 px | Implemented; automated overflow checks pass; manual audit still recommended |
| Faculty-only completion tracker for own subjects | Yes — JWT identity + active selection |
| Submitted/pending counts and percentage | Yes |
| Verified eligibility data only | Yes — explicit roster table |
| Never reveal who submitted ratings/comments | Yes — no feedback IDs/content; pending list only |
| Professional pending-student PDF | Yes |
| PDF has subject/year/semester/faculty/period, counts, percentage | Yes |
| No feedback details or internal IDs in PDF | Yes |
| Prepared WhatsApp message, user-controlled sharing | Yes |
| No automatic sending, scraping or phone-number exposure | Yes |
| Tests for PWA, responsive flows, tracker auth/anonymity, PDF, WhatsApp, regressions | Yes (see section 8) |
| No production deployment or production data change | Yes |
| Detailed completion report in the repository | This document |
