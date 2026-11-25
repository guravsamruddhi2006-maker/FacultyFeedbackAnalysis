# 22 — Future Enhancements

> **FacultyInsight AI** · Documentation set · [Back to index](../README.md#documentation-index)

A realistic roadmap. Items are grouped by value and effort, and each notes what it would touch.

## 22.1 Guiding principles

1. Keep the system **explainable** — no opaque AI claims.
2. Keep migrations **additive** and data **recoverable**.
3. Protect **student anonymity** in every new feature.
4. Prefer **small, testable increments** over rewrites.
5. Stay **free-tier friendly** where possible.

## 22.2 High value, low effort

| Enhancement | What it involves | Touches |
|-------------|------------------|---------|
| **Password reset by admin** | Admin-triggered reset with a one-time temporary password | `api/admin.py`, `AdminManagement.tsx` |
| **Bulk student import** | CSV upload with validation and a dry-run preview | new admin endpoint + UI |
| **Period reminders banner** | Show remaining days on the student dashboard | `StudentDashboard.tsx` |
| **Better empty states** | Explain *why* no offerings appear | student/faculty pages |
| **Question reordering** | `display_order` column and ordering in queries | schema + catalog |
| **Export audit log** | CSV download of filtered audit rows | `api/admin.py`, `report_service.py` |
| **Accessibility pass** | Keyboard traps, labels, focus styles, contrast | `components/ui.tsx`, pages |
| **Consistent error copy** | Map API errors to actionable messages | `lib/api.ts`, pages |

## 22.3 Analytics and insight improvements

| Enhancement | What it involves | Notes |
|-------------|------------------|-------|
| **Confidence intervals** | Wilson/normal intervals per question | Requires response counts; cheap |
| **Minimum-response suppression** | Hide comments for groups below a threshold | Strengthens anonymity |
| **Per-question trend lines** | Trend per question, not just overall | Extend `build_trend_insights` |
| **Cohort comparison** | Compare semesters or years side by side | Admin view |
| **Weighted averages** | Optional question weights | Add a `weight` column |
| **Comment deduplication** | Collapse near-duplicate comments | Simple similarity |
| **Exportable insight JSON** | Machine-readable insights | New endpoint |

## 22.4 AI / NLP improvements

| Enhancement | What it involves | Prerequisites |
|-------------|------------------|---------------|
| **Larger labelled dataset** | Collect and annotate real comments | Consent + governance |
| **Validated classifier** | Train, evaluate, record metrics | Real data, class balance |
| **Set `validated: true`** | Only after genuine evaluation | Documented metrics |
| **Multilingual sentiment** | Language detection + lexicons/models | Translation or per-language models |
| **Aspect-based sentiment** | Sentiment per topic, not per comment | Topic model + labels |
| **Abstractive summaries** | Optional LLM summary of themes | Privacy review, cost control |
| **Model monitoring** | Track drift and disagreement | Logging + evaluation set |

> Do not flip `"validated": true` until the evaluation genuinely supports it. A false claim is worse than no model.

## 22.5 Security and operations

| Enhancement | What it involves | Priority |
|-------------|------------------|----------|
| **Global rate limiting** | Redis/Upstash-backed limiter | High for public deployments |
| **Token revocation** | Short-lived access + refresh, or a denylist | Medium |
| **Multi-factor authentication** | TOTP for admins | High |
| **Content Security Policy** | Strict CSP headers | High |
| **Automated dependency scanning** | Dependabot/`pip-audit`/`npm audit` in CI | High |
| **CI pipeline** | GitHub Actions with Postgres service | High |
| **Structured logging** | JSON logs with request IDs | Medium |
| **Error tracking** | Sentry or similar | Medium |
| **Backup automation** | Scheduled `pg_dump` + retention | High |
| **Restore drill** | Documented quarterly test | High |
| **Secret scanning** | Pre-commit hooks and GitHub scanning | High |

## 22.6 Product features

| Feature | Description | Effort |
|---------|-------------|--------|
| **Email notifications** | Period open/close, approval decisions | Medium |
| **Department-scoped admins** | Admin sees only their department | High (multi-tenant) |
| **Multi-department support** | Tenancy, scoping, reporting | High |
| **Faculty development plans** | Link insights to actions and follow-up | Medium |
| **Student feedback history** | A read-only personal archive | Low |
| **Saved report templates** | Reusable filter presets | Low |
| **Scheduled reports** | Email a PDF at period close | Medium |
| **Public transparency report** | Aggregated, anonymised department summary | Medium |
| **Mobile PWA** | Installable, offline shell | Medium |

## 22.7 Data and reporting

| Enhancement | Description |
|-------------|-------------|
| **Streaming exports** | Avoid the 30-second serverless limit |
| **Scheduled archiving** | Move old feedback to cold storage |
| **Data retention policy** | Configurable purge after N years |
| **Anonymised research export** | Strip identifiers, add a data dictionary |
| **Data-subject export** | Per-user bundle for privacy requests |
| **Soft-delete audit** | Track every deletion, not just audited actions |

## 22.8 Developer experience

| Enhancement | Description |
|-------------|-------------|
| **OpenAPI-generated client** | Typed frontend client from the schema |
| **Storybook** | Component catalogue |
| **More component tests** | Cover dashboards and forms |
| **Playwright E2E** | Full role journeys in CI |
| **Seed script for demos** | Sample faculty/students/feedback for demos (clearly marked non-production) |
| **Makefile / task runner** | One command for setup, test, build |
| **Pre-commit hooks** | Format, lint, type-check, secret scan |
| **Container health checks** | Compose-level readiness for backend |

## 22.9 Suggested sequence

A pragmatic order for a student team continuing the project:

1. **CI + dependency scanning** — protects every later change.
2. **CSP and global rate limiting** — closes the biggest web risks.
3. **Admin password reset + bulk import** — removes the most common manual work.
4. **Accessibility and empty-state pass** — visible quality improvement.
5. **Confidence intervals + minimum-response suppression** — better and safer analytics.
6. **Email notifications** — improves participation.
7. **Validated sentiment model** — only with real, consented data.
8. **Multi-department support** — only if the institution needs it.

## 22.10 Explicit non-goals

To keep scope honest, these are **not** planned:

- Becoming a full LMS (grades, assignments, attendance).
- Storing payment or financial data.
- Selling or sharing data with third parties.
- Autonomous decisions about faculty based on sentiment scores.
- Presenting an unvalidated model as authoritative.

## 22.11 How to propose a change

1. Open an issue describing the problem, not just the solution.
2. Note privacy and migration impact.
3. Add tests for the new behaviour.
4. Keep the change additive and reversible.
5. Update the relevant document in this `docs/` set.

## 22.12 Related documents

- [14 — Analytics and AI](./14-analytics-and-ai.md)
- [15 — Security and Privacy](./15-security-and-privacy.md)
- [18 — Testing](./18-testing.md)
- [20 — Known Limitations](./20-known-limitations.md)

---

[Back to the documentation index](../README.md#documentation-index)
