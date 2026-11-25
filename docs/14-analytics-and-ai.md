# 14 — Analytics and AI

> **FacultyInsight AI** · Documentation set · [Back to index](../README.md#documentation-index)

This page explains exactly how the numbers and the "AI" features are produced — and what they do **not** claim.

## 14.1 Honest summary

| Capability | Status | Method |
|------------|--------|--------|
| Rating averages, counts, distributions | **Active** | SQL aggregation |
| Question-level averages | **Active** | SQL aggregation |
| Trends across academic years | **Active** | Aggregated ratings |
| Strengths and improvement areas | **Active** | Threshold rules |
| Recommendations | **Active** | Keyword-matched library |
| Topic classification | **Active** | Keyword buckets |
| Keyword extraction | **Active** | Unigram/bigram frequency |
| Sentiment | **Active** | `lexicon-v1` rule-based baseline |
| Trained TF-IDF sentiment classifier | **Not active** | Metadata `"validated": false` |

The application never presents a heuristic as a validated machine-learning model. The `method` and `limitations` fields travel with the data.

## 14.2 Where analytics come from

All analytics are computed from real rows in `feedback` and `feedback_answer`, joined through `course_offerings`, `subjects`, `faculty`, `academic_years` and `semesters`.

There is no hardcoded sample data, no synthetic scores and no pre-computed cache. If there is no feedback, the numbers are zero or empty.

### Common filters

| Filter | Applies to |
|--------|-----------|
| `academic_year` | Offerings |
| `semester_number` | Offerings |
| `subject_code` | Offerings |
| `faculty_id` | Offerings (admin views) |

### Metrics

| Metric | Definition |
|--------|-----------|
| Response count | Number of feedback rows |
| Average rating | Mean of all `feedback_answer.rating` values (1–5) |
| Question average | Mean per `question_id` |
| Distribution | Count of each rating value |
| Trend | Average per academic year, ordered |

## 14.3 Strengths and improvement areas

Defined in `backend/app/services/insights.py`:

| Constant | Value |
|----------|-------|
| `STRENGTH_THRESHOLD` | `4.0` |
| `STRENGTH_MIN_RESPONSES` | `3` |
| `IMPROVEMENT_THRESHOLD` | `3.0` |
| `IMPROVEMENT_MIN_RESPONSES` | `3` |

Rules:

- A question is a **strength** when its average is **≥ 4.0** and it has **≥ 3** responses.
- A question is an **improvement area** when its average is **≤ 3.0** and it has **≥ 3** responses.
- With fewer than 3 responses, no strength or weakness is declared. This prevents a single comment from dominating the narrative.

Each improvement area includes the average, the response count and a recommendation.

## 14.4 Recommendations

The recommendation library maps question keywords to actions:

| Keyword in question | Recommendation |
|---------------------|----------------|
| `practical` | Include more real-world, hands-on examples and live demonstrations. |
| `syllabus` | Review syllabus pacing and redistribute topics to protect coverage. |
| `pace` | Adjust the teaching pace and schedule additional revision sessions. |
| `clarity` | Increase concept-clarification opportunities such as worked examples and checks for understanding. |
| `participation` | Add structured interactive activities and peer discussion slots. |
| `knowledge` | Reinforce deeper subject knowledge through doubt-clearing sessions and advanced references. |
| `example` | Include more practical examples and real-world case studies. |
| *(no match)* | Schedule a follow-up feedback cycle after pedagogical adjustments. |

Every recommendation carries a rationale of the form:

> Reported by **N** student(s) with an average rating of **X.XX/5**.

So a reader can see the evidence behind each suggestion.

## 14.5 Trend insights

`build_trend_insights` compares the earliest and latest academic years with data:

- fewer than two periods with responses → no trend insight;
- `delta > 0.05` → `improving`;
- `delta < -0.05` → `declining`;
- otherwise → `stable`.

Each insight includes the current and previous averages, the change, the response count and the evidence string.

## 14.6 Sentiment — the active engine

The default and currently active engine is **`lexicon-v1`**, implemented in `backend/app/analytics/text.py`.

### How it works

1. Lowercase and clean the text.
2. Tokenise into words.
3. Score each token: `+1` for a positive word, `-1` for a negative word.
4. Apply an **intensifier** multiplier if the previous word is `very`, `really`, `extremely`, etc.
5. Flip the sign if a negation (`not`, `never`, `no`, …) appears in the previous three tokens.
6. Sum the scores.
7. Label:
   - `score > 0.2` → `positive`
   - `score < -0.2` → `negative`
   - otherwise → `neutral`
8. Compute a heuristic `confidence` from the score strength.

### Output

```json
{
  "label": "positive",
  "score": 1.35,
  "confidence": 0.72,
  "matched_terms": ["clear", "useful"],
  "method": "lexicon-v1",
  "limitations": "Heuristic lexicon baseline. Not a validated ML probability."
}
```

### What `confidence` means

It is a **heuristic strength score**, not a calibrated probability. Do not report it as "72% certain".

### Known weaknesses

- Sarcasm and negation scopes beyond three tokens are not handled well.
- Domain-specific words may be missing from the lexicon.
- It is English-only.
- It is a baseline, not a trained model.

## 14.7 Topic classification

Comments are bucketed into eight topics by keyword overlap:

| Topic | Example keywords |
|-------|------------------|
| Teaching clarity | clear, explain, understand, concept, confusing |
| Subject knowledge | knowledge, expert, doubt, answer, deep |
| Classroom interaction | interactive, participate, engage, discussion |
| Practical examples | practical, example, real, industry, demo |
| Syllabus completion | syllabus, complete, coverage, portions, late |
| Teaching pace | pace, fast, slow, rushed, speed |
| Assessment and feedback | exam, marks, assignment, grading, evaluation |
| Support and accessibility | support, helpful, accessible, available, approachable |

Each topic reports `mentions` and a positive/neutral/negative split based on the sentiment of the matching comments.

A comment can match multiple topics. Topic counts are **not** exclusive.

## 14.8 Keyword extraction

`extract_keywords` counts unigrams and bigrams across comments and returns the top terms by weight (bigrams weighted 1.4×). This is a frequency heuristic, not TF-IDF at request time.

The optional offline training pipeline (`ml/train.py`) does use TF-IDF, but that is separate from the request-time keyword list.

## 14.9 The optional TF-IDF classifier

The repository contains:

```text
ml/train.py
ml/data/sentiment_labeled.csv
ml/models/sentiment_model_metadata.json
ml/models/sentiment_model.joblib   (if trained)
```

### Why it is not active

`_load_trained_model()` loads the classifier **only if**:

1. both the `.joblib` file and the metadata file exist; **and**
2. the metadata contains `"validated": true`.

The committed metadata currently says:

```json
{
  "validated": false,
  "metrics": { "accuracy": 0.3333, "macro_f1": 0.1667, ... }
}
```

Therefore `sentiment_engine_info()` reports:

```json
{
  "active_engine": "lexicon-v1",
  "validated": false,
  "metrics": {},
  "trained_at": null,
  "limitations": "Transparent rule-based lexicon baseline. It has not been evaluated as a statistical ML model."
}
```

The low accuracy is a property of the tiny sample dataset, not a bug in the loader. The system correctly refuses to present it as validated.

### Enabling it responsibly

Only after training on a real, sufficiently large, class-balanced dataset:

1. Run `ml/train.py` with the dataset.
2. Review the metrics and confusion matrix.
3. Set `"validated": true` in the metadata **only if** the evaluation genuinely supports it.
4. Restart the API process so the `lru_cache` reloads.

Until then, leave it false. See [22 — Future Enhancements](./22-future-enhancements.md).

## 14.10 API surface for analytics

| Endpoint | Purpose |
|----------|---------|
| `GET /api/analytics/faculty/me` | Faculty's own aggregates |
| `GET /api/analytics/faculty/me/comparison` | Own performance across earlier offerings |
| `GET /api/analytics/admin` | Department aggregates |
| `GET /api/analytics/admin/faculty/{id}` | One faculty (admin) |
| `GET /api/analytics/admin/faculty-comparison` | Department comparison |
| `GET /api/ml/model-info` | Active engine metadata |
| `POST /api/ml/sentiment` | Classify up to 50 texts |
| `GET /api/ml/insights` | Faculty insight bundle |

## 14.11 How to read the numbers responsibly

- **Small samples are noisy.** Below 3 responses, the system refuses to label strengths or weaknesses.
- **Averages hide spread.** Always look at the distribution too.
- **Sentiment is a hint.** Read the comments; the lexicon can misread sarcasm.
- **Correlation is not causation.** A trend does not prove a teaching change caused it.
- **Anonymity has a limit.** In a very small class, a distinctive comment may be recognisable. Do not quote comments in a way that identifies a student.

## 14.12 Related documents

- [05 — Database Schema](./05-database-schema.md)
- [13 — Feedback Lifecycle](./13-feedback-lifecycle.md)
- [20 — Known Limitations](./20-known-limitations.md)
- [22 — Future Enhancements](./22-future-enhancements.md)

---

**Next:** [15 — Security and Privacy →](./15-security-and-privacy.md)
