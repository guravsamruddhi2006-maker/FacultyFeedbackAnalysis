# 21 — Glossary

> **FacultyInsight AI** · Documentation set · [Back to index](../README.md#documentation-index)

Terms used across the codebase and this documentation.

## 21.1 Domain terms

| Term | Meaning |
|------|---------|
| **Academic year** | A period such as `2025-26`, stored as `VARCHAR(9)` and validated by a `YYYY-YY` check. |
| **Semester** | A number from 1 to 8. Semester 8 is internship-only and has no seeded subjects. |
| **Department** | The organisational unit. The seed creates `Computer Science and Engineering` (`CSE`). |
| **Subject** | A catalog course with a code, name and semester. |
| **Faculty** | A teacher account, identified by email. |
| **Student** | A learner account, identified by USN. |
| **Administrator** | A privileged account that manages the catalog and accounts. |
| **USN** | University Serial Number; the student's login identifier. Pattern `^[A-Za-z0-9]{6,50}$`. |
| **Offering** | A concrete instance of a subject taught by a faculty member in a year and semester. Feedback attaches to an offering. |
| **Selection** | A faculty member's declaration that they teach a subject in a year and semester. |
| **Subject request** | A faculty request to add a missing subject to the catalog. |
| **Feedback period** | The date window in which students may submit feedback for a year and semester. |
| **Question** | A rating prompt (1–5) shown on the feedback form. |
| **Rating** | An integer from 1 (very poor) to 5 (excellent). |
| **Comment** | Free-text feedback, 10–1000 characters. |
| **Insight** | A strength, improvement area, recommendation or trend derived from data. |
| **Audit log** | A record of sensitive actions with actor, action, entity, details and IP. |

## 21.2 Technical terms

| Term | Meaning |
|------|---------|
| **API** | Application Programming Interface; here, the JSON HTTP interface under `/api`. |
| **ASGI** | Asynchronous Server Gateway Interface; the standard FastAPI/Uvicorn follow. |
| **JWT** | JSON Web Token; a signed token carrying `sub`, `role`, `iat`, `exp`. |
| **HS256** | HMAC-SHA256, the JWT signing algorithm used. |
| **bcrypt** | A slow password-hashing algorithm resistant to brute force. |
| **RBAC** | Role-Based Access Control; student, faculty, admin. |
| **CORS** | Cross-Origin Resource Sharing; the browser rule for cross-origin API calls. |
| **SPA** | Single-Page Application; the React frontend. |
| **SPA fallback** | Serving `index.html` for unknown paths so client-side routes work. |
| **Serverless function** | A function run on demand by a host (here, Vercel) with a time limit. |
| **Cold start** | Extra latency when a serverless instance starts after idle. |
| **Migration** | A versioned database change. |
| **Additive migration** | A migration that only creates/alters, never drops or truncates. |
| **Advisory lock** | A PostgreSQL lock used to serialise concurrent schema upgrades. |
| **Idempotent** | Safe to run more than once with the same result. |
| **Parameterised query** | A SQL query that binds values separately from the SQL text, preventing injection. |
| **Seed data** | Reference rows inserted on setup (departments, semesters, years, questions, subjects). |
| **Bootstrap** | An endpoint that inserts base reference data if missing. |
| **Health check** | An endpoint that reports whether the service/database is alive. |

## 21.3 Analytics and AI terms

| Term | Meaning |
|------|---------|
| **Aggregate** | A summary computed from many rows, such as an average. |
| **Distribution** | The count of each rating value. |
| **Trend** | Change in average rating across academic years. |
| **Strength** | A question averaging ≥ 4.0 with ≥ 3 responses. |
| **Improvement area** | A question averaging ≤ 3.0 with ≥ 3 responses. |
| **Recommendation** | A suggested action tied to an improvement area. |
| **Lexicon** | A word list with positive/negative polarity. |
| **Sentiment** | A label (`positive`, `neutral`, `negative`) with a score. |
| **Negation** | A word such as `not` that flips polarity. |
| **Intensifier** | A word such as `very` that scales polarity. |
| **Topic** | A keyword bucket such as "Teaching clarity". |
| **Keyword** | A frequent unigram or bigram in comments. |
| **TF-IDF** | Term Frequency–Inverse Document Frequency; a text vectorisation method used by the optional model. |
| **Classifier** | A model that assigns a label; here, the optional TF-IDF + logistic regression model. |
| **Validated** | Metadata flag meaning a model passed an evaluation. Currently `false`. |
| **Explainable** | A method whose reasoning can be inspected (the lexicon shows matched terms). |

## 21.4 Operations terms

| Term | Meaning |
|------|---------|
| **Environment variable** | Configuration supplied outside the code, such as `DATABASE_URL`. |
| **`.env`** | A local file of environment variables; never committed. |
| **Secret** | A credential such as a JWT key or database password. |
| **Rotation** | Replacing a secret with a new value. |
| **Backup** | A copy of the database for recovery. |
| **Restore** | Rebuilding a database from a backup. |
| **Rate limit** | A cap on attempts per time window. |
| **Audit trail** | The history of sensitive actions. |
| **Least privilege** | Giving each role only the access it needs. |

## 21.5 Acronyms

| Acronym | Expansion |
|---------|-----------|
| API | Application Programming Interface |
| CORS | Cross-Origin Resource Sharing |
| CSV | Comma-Separated Values |
| CSE | Computer Science and Engineering |
| DB | Database |
| E2E | End-to-End |
| FK | Foreign Key |
| HTTP | Hypertext Transfer Protocol |
| HTTPS | HTTP Secure |
| JWT | JSON Web Token |
| ML | Machine Learning |
| NLP | Natural Language Processing |
| PDF | Portable Document Format |
| PK | Primary Key |
| RBAC | Role-Based Access Control |
| SPA | Single-Page Application |
| SQL | Structured Query Language |
| UI | User Interface |
| USN | University Serial Number |
| UX | User Experience |

## 21.6 Related documents

- [01 — Project Overview](./01-project-overview.md)
- [05 — Database Schema](./05-database-schema.md)
- [14 — Analytics and AI](./14-analytics-and-ai.md)

---

**Next:** [22 — Future Enhancements →](./22-future-enhancements.md)
