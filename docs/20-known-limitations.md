# 20 — Known Limitations

> **FacultyInsight AI** · Documentation set · [Back to index](../README.md#documentation-index)

Honest scope boundaries. These are deliberate trade-offs or known gaps, not hidden defects.

## 20.1 Product scope

| Limitation | Detail |
|------------|--------|
| Single department | Designed around one CSE department. Multi-department tenancy is not implemented. |
| No admin assignment of subjects | Faculty declare their own teaching load; admins approve requests but do not assign. |
| No notifications | No email, SMS or push. Users must check the app. |
| No chat or messaging | Not a communication platform. |
| No mobile app | Responsive web only. |
| English only | UI and NLP are English. |
| No offline mode | Requires network access. |

## 20.2 AI / ML

| Limitation | Detail |
|------------|--------|
| Sentiment is a lexicon baseline | `lexicon-v1` is rule-based and explainable, not a validated model. |
| TF-IDF classifier inactive | Metadata says `"validated": false`; accuracy on the tiny sample is 0.3333. |
| No sarcasm/irony handling | Negation is only checked in a three-token window. |
| No calibrated confidence | The reported `confidence` is a heuristic strength score. |
| Topic counts overlap | A comment can match several topics. |
| Keyword extraction is frequency-based | Not TF-IDF at request time. |
| No generative AI | No LLM summaries, chatbots or auto-written reports. |

## 20.3 Analytics

| Limitation | Detail |
|------------|--------|
| Small-sample noise | Below 3 responses, no strength/weakness is declared. |
| Averages hide spread | Distribution must be read alongside the mean. |
| No statistical significance testing | No p-values or confidence intervals. |
| No causal inference | Trends are descriptive. |
| No per-question weighting | Every question contributes equally. |
| No cohort comparison by student group | No demographic breakdowns (which also protects privacy). |

## 20.4 Security and operations

| Limitation | Detail |
|------------|--------|
| Rate limiter is per process | On Vercel it is per warm instance, not global. |
| No token revocation list | JWTs remain valid until expiry (30 min default). Logout is client-side. |
| No MFA | Single-factor passwords. |
| No SSO / LDAP | Local accounts only. |
| No password-reset email | Recovery is operator-only. |
| No WAF | Relies on the host's protections. |
| No automated vulnerability scanning | Manual review only. |
| No CI pipeline | Tests run manually. |

## 20.5 Database and migrations

| Limitation | Detail |
|------------|--------|
| Forward-only migrations | No destructive down-migrations. |
| Runtime upgrade on first request | Adds latency to the first request after a cold start. |
| No partitioning/archiving | Feedback grows in one table. |
| No read replica | All queries hit the primary. |
| Reports generated in memory | Very large exports can hit the 30-second serverless limit. |

## 20.6 Deployment

| Limitation | Detail |
|------------|--------|
| 30-second function limit | Long reports may time out on Vercel. |
| Cold starts | Serverless latency after idle. |
| Neon free-tier suspend | First request after idle is slower. |
| Single region | No multi-region failover. |
| Docker Compose defaults are insecure | Must be hardened before exposure. |

## 20.7 Anonymity limits

- `feedback.student_id` is stored to enforce one submission per offering. It is not exposed by any endpoint, but it exists in the database.
- In a very small class, a distinctive free-text comment may be recognisable even without an identifier.
- Administrators with direct database access can technically join tables. This is an operator-trust boundary, not a cryptographic guarantee.
- No differential privacy or k-anonymity suppression is applied to comment display.

## 20.8 Frontend

| Limitation | Detail |
|------------|--------|
| Token in `localStorage` | Readable by JavaScript; XSS would expose it. CSP is not configured in the app. |
| No offline caching | Every load needs the network. |
| Limited component tests | Three test files; no full browser E2E in the default suite. |
| No internationalisation | English strings are inline. |
| No dark mode | Not implemented. |

## 20.9 Data lifecycle

| Limitation | Detail |
|------------|--------|
| No automated retention policy | Data is kept until manually removed. |
| No self-service account deletion | Admins deactivate accounts. |
| No export of personal data | Reports export aggregates/comments, not a user data bundle. |
| No soft-delete audit for every table | Only audited actions are recorded. |

## 20.10 Repository hygiene notes

- The repository is public. Earlier commits contained local-only development credentials in reports; the current tree redacts them. Rotate any credential that was ever committed.
- Root-level `*.md` files are historical reports and may describe older states. This `docs/` set is the maintained source of truth.
- `database/backups/` and `.env` files must never be committed.
- Temporary admin-recovery files must be deleted after use.

## 20.11 What is intentionally out of scope

- Payments, fees or finance.
- Attendance tracking.
- Timetable scheduling.
- Learning management features (assignments, grades).
- Multi-college federation.
- Native mobile apps.

## 20.12 Related documents

- [14 — Analytics and AI](./14-analytics-and-ai.md)
- [15 — Security and Privacy](./15-security-and-privacy.md)
- [22 — Future Enhancements](./22-future-enhancements.md)

---

**Next:** [21 — Glossary →](./21-glossary.md)
