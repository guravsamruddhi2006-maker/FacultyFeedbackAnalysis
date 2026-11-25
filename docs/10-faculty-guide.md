# 10 — Faculty Guide

> **FacultyInsight AI** · Documentation set · [Back to index](../README.md#documentation-index)

This guide covers faculty registration, subject selection, analytics, comments and reports.

## 10.1 Register and get approved

1. Go to **`/register/faculty`**.
2. Enter your full name, email, department and a password (8+ characters, letter + number).
3. Submit.

Your account is created with status **`pending`**. You cannot sign in until an administrator approves it.

If you try to sign in while pending, the API returns a message explaining that the account is awaiting approval.

## 10.2 Sign in

1. Go to **`/login`** and choose the **Faculty** tab.
2. Enter your email and password.

You land on **`/faculty`**.

## 10.3 Teaching overview (`/faculty`)

The dashboard shows only **your** data. Use the filters to narrow it:

- academic year;
- semester;
- subject.

### What you see

| Section | Content |
|---------|---------|
| Summary tiles | Feedback responses, average rating, selected subjects, year-over-year change |
| My subjects and semesters | The offerings you currently teach |
| Question-wise performance | Average score per feedback question |
| Academic-year comparison | Performance across periods |
| Evidence-based insights | Strengths, improvement areas and recommendations |
| Strengths | Questions averaging **≥ 4.0** with at least **3** responses |
| Areas for improvement | Questions averaging **< 3.0** with at least **3** responses |
| Sentiment and recurring topics | Comment polarity and keyword themes |
| Anonymous student comments | Filterable comment list |

If there are fewer than 3 responses, the insight engine does not declare a strength or weakness. This avoids over-reacting to one comment.

### Export your report

Use **Export CSV** or **Export PDF**. The export contains only your own data and never includes student identifiers.

## 10.4 My subjects (`/faculty/subjects`)

This is where you declare what you teach.

### Add a subject

1. Click **Add subject**.
2. Pick a subject from the catalog. Its semester is filled automatically.
3. Choose the academic year and semester.
4. Save.

Adding a selection automatically creates the matching **course offering** so students can see it.

Rules:

- You can only select subjects that exist in the catalog.
- The subject's semester and the selection's semester must be consistent.
- You cannot create a duplicate selection for the same subject, year and semester.
- Your account must be approved.

### Edit a selection

You can change the subject, year or semester. If the selection already has feedback, the API refuses the edit with `409` to protect history. In that case, deactivate it and add a new selection if genuinely needed.

### Remove a selection

Removing a selection **deactivates** it rather than deleting your history:

- if the offering has no feedback, it is deleted;
- if it has feedback, the offering is kept for reporting.

### Request a missing subject

If the subject is not in the catalog:

1. Click **Request subject**.
2. Enter the subject code, name and semester.
3. Submit.

The request goes to the administrator. Approval only adds the subject to the catalog — you still need to add it as a selection afterwards.

See [12 — Subject Selection and Requests](./12-subject-selection-and-requests.md) for the full rules.

## 10.5 Student comments (`/faculty/comments`)

This page lists anonymised comments for your offerings.

- Comments are shown without any student identifier.
- You can filter by year, semester, subject and sentiment.
- Comments are the raw text students wrote; sentiment labels are computed by the NLP engine.

## 10.6 Trends and sentiment

- **Trends** compare average ratings across academic periods for your subjects.
- **Sentiment** summarises comment polarity using the active `lexicon-v1` engine.

These are descriptive statistics. Read [14 — Analytics and AI](./14-analytics-and-ai.md) before quoting them in a review — the sentiment engine is a transparent baseline, not a validated ML model.

## 10.7 My profile (`/faculty/profile`)

Shows your name, email, department and account status. Use **Change password** to update your password.

## 10.8 Reports

| Format | Contents |
|--------|----------|
| CSV | Summary metrics, question averages, comment list |
| PDF | Formatted report with the same data |

Filters apply to the export. The report is generated from the same queries as the dashboard, so the numbers match.

## 10.9 Privacy commitments

- You see only your own offerings and feedback.
- You never see which student submitted which comment.
- Administrators see department aggregates and comments, not student identities.
- Your email is visible to administrators but not to students.

## 10.10 Common questions

**Why can't students see my subject?**
Check that (a) your account is approved, (b) you added an active selection for the correct year and semester, and (c) the administrator has opened a feedback period for that year and semester.

**Why is my average different from last week?**
Averages change when new feedback arrives or when you change the filters. The dashboard always reflects current data.

**Can I delete a comment?**
No. Comments are part of the feedback record. If a comment is abusive, contact the administrator.

**Can I see who wrote a comment?**
No, by design.

## 10.11 Related documents

- [12 — Subject Selection and Requests](./12-subject-selection-and-requests.md)
- [13 — Feedback Lifecycle](./13-feedback-lifecycle.md)
- [14 — Analytics and AI](./14-analytics-and-ai.md)

---

**Next:** [11 — Administrator Guide →](./11-administrator-guide.md)
