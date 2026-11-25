# 12 — Subject Selection and Requests

> **FacultyInsight AI** · Documentation set · [Back to index](../README.md#documentation-index)

This is the most important business rule in the system: **who decides which subjects a faculty member teaches, and how does a subject become visible to students?**

## 12.1 The chain

```text
Catalog subject
      │  faculty chooses
      ▼
faculty_subject_selections (active, for a year + semester)
      │  creates / reuses
      ▼
course_offerings (subject + year + semester + faculty)
      │  requires an open period
      ▼
Student sees the offering and can submit feedback
```

Each link is required. Missing any one means the student sees nothing.

## 12.2 Who does what

| Actor | Can do | Cannot do |
|-------|--------|-----------|
| Faculty | Add, edit and remove **their own** selections; request missing subjects | Assign subjects to other faculty |
| Administrator | Approve/reject subject requests; manage the catalog | Assign a subject to a faculty member |
| Student | View offerings and submit feedback | Change selections or offerings |

This is deliberate. Teaching load is a professional declaration by faculty, reviewed through the catalog and the request process — not an administrative assignment.

## 12.3 Selection rules

A selection is the tuple:

```text
(faculty_id, subject_code, academic_year, semester_number)
```

Rules enforced by the API and the database:

1. **Faculty must be approved.** Pending, rejected or inactive accounts cannot create selections.
2. **The subject must exist** in `subjects`.
3. **Semester consistency.** The selected semester must match the subject's catalog semester.
4. **No duplicates.** A unique constraint prevents the same tuple twice.
5. **Year and semester must exist** in the reference tables.
6. **The faculty member can only touch their own selections.** The `faculty_id` comes from the token, never from the request body.

## 12.4 What happens when a selection is added

In one transaction the API:

1. inserts the `faculty_subject_selections` row with `is_active = TRUE`;
2. inserts the matching `course_offerings` row if it does not already exist;
3. writes an audit entry.

The offering is what students actually see. It is unique on:

```text
(academic_year, semester_number, subject_code, faculty_id)
```

Two faculty members can teach the same subject in the same semester; each gets a separate offering and separate feedback.

## 12.5 What happens when a selection is removed

Removal is **deactivation**, not deletion:

| Situation | Result |
|-----------|--------|
| Offering has **no** feedback | Selection deactivated; offering deleted |
| Offering **has** feedback | Selection deactivated; offering kept for historical reporting |

This is why historical averages never suddenly lose data when a faculty member stops teaching a subject.

## 12.6 What happens when a selection is edited

Editing changes the subject, year or semester. The API:

- re-validates all the rules above;
- refuses with **`409`** if the existing offering already has feedback, because changing it would re-attribute historical feedback;
- otherwise updates the selection and reconciles the offering.

If you genuinely need to move a subject with feedback, deactivate the old selection and add a new one.

## 12.7 Student visibility rule (exact)

An offering is visible to a student only when **all** of these are true:

```sql
-- simplified
JOIN faculty_subject_selections fss
  ON fss.faculty_id = co.faculty_id
 AND fss.subject_code = co.subject_code
 AND fss.academic_year = co.academic_year
 AND fss.semester_number = co.semester_number
 AND fss.is_active = TRUE
JOIN faculty f ON f.faculty_id = co.faculty_id
 AND f.status = 'approved'
```

The same fragment (`ACTIVE_SELECTION_JOIN`) is reused by every student-facing query, so the rule cannot drift between endpoints.

## 12.8 Subject requests

If a subject is missing from the catalog, faculty request it.

### Request

```json
POST /api/faculty/me/subject-requests
{
  "subject_code": "CS599",
  "subject_name": "Applied Deep Learning",
  "semester_number": 6
}
```

### Rules

- code ≥ 2 characters, name ≥ 3 characters, semester 1–8;
- the faculty account must be approved;
- only **one pending request per subject code** at a time (partial unique index);
- the request is stored in `subject_requests` with `status = 'pending'`.

### Review

An administrator approves or rejects with an optional note:

```json
PATCH /api/admin/subject-requests/7
{ "status": "approved", "admin_note": "Added to semester 6." }
```

| Outcome | Effect |
|---------|--------|
| Approved | Subject inserted into `subjects` if absent; request marked approved; reviewer and timestamp recorded |
| Rejected | Request marked rejected with the note |

**Approval does not create a selection or offering.** The faculty member still adds the subject from `/faculty/subjects`. This keeps the "faculty declare their own load" rule intact.

## 12.9 Worked example

**Goal:** Dr. Iyer teaches Machine Learning (CS501) to semester 5 in 2025-26.

1. Administrator confirms `CS501` exists in the catalog for semester 5.
2. Dr. Iyer signs in and opens **My subjects**.
3. She adds `CS501`, year `2025-26`, semester `5`.
4. The API inserts the selection and creates offering `#12`.
5. The administrator opens a feedback period for `2025-26` / semester `5`.
6. Students filtering to that year and semester now see offering `#12` as **pending**.
7. Students submit feedback.
8. Dr. Iyer sees the aggregates; the administrator sees department totals.

**Variant:** `CS501` is missing from the catalog.

1. Dr. Iyer submits a subject request.
2. The administrator approves it; `CS501` is added to the catalog.
3. Dr. Iyer returns to **My subjects** and adds the selection.
4. The rest of the flow is identical.

## 12.10 Common mistakes

| Symptom | Cause | Fix |
|---------|-------|-----|
| Students see no offerings | No active selection, or faculty not approved | Approve faculty; ask them to add the subject |
| Selection rejected as duplicate | The tuple already exists | Edit the existing selection |
| `409` when editing | The offering already has feedback | Deactivate and create a new selection |
| Subject request stuck | Administrator has not reviewed it | Check `/admin/subject-requests` |
| Approved request but still no offering | Approval only adds to the catalog | Faculty must add the selection |

## 12.11 Related documents

- [05 — Database Schema](./05-database-schema.md)
- [10 — Faculty Guide](./10-faculty-guide.md)
- [11 — Administrator Guide](./11-administrator-guide.md)
- [13 — Feedback Lifecycle](./13-feedback-lifecycle.md)

---

**Next:** [13 — Feedback Lifecycle →](./13-feedback-lifecycle.md)
