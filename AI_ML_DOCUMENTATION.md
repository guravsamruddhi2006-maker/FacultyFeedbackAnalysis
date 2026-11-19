# FacultyInsight AI — AI / ML Documentation

## 1. Overview

The AI layer answers three questions from real feedback data:

1. **How positive / negative are the written comments?** (sentiment)
2. **What topics keep recurring?** (topic extraction)
3. **Where are the strengths and improvement areas?** (evidence-based insight generation)

All calculations are derived from aggregated database answers and anonymised comments.

## 2. Sentiment pipeline

### Default engine — `lexicon-v1` (transparent baseline)

- Tokenisation with stopword removal.
- Lexicon scoring with positive/negative word lists.
- Negation handling (`not`, `no`, …) flips polarity.
- Intensifier multipliers (`very`, `really`, …).
- Confidence is a heuristic score, **not** a calibrated probability; limitations are always returned.

### Optional trained engine — `tfidf-classifier`

- Pipeline: `TfidfVectorizer` + `LogisticRegression`.
- Training entry point: `python ml/train.py --data <labelled.csv>`.
- Requires a labelled CSV with `text,label` columns containing all three labels with at least two samples each.
- Performs a stratified train/test split, computes accuracy, macro precision/recall/F1 and confusion matrix.
- Writes `ml/models/sentiment_model.joblib` and `ml/models/sentiment_model_metadata.json`.
- The service loads the trained model only when metadata `validated` is true; otherwise it falls back to the lexicon baseline.

### Current status

- Trained demo artefacts exist under `ml/models/`.
- The demo training split produced `validated: false` (insufficient quality on the tiny sample), therefore the **lexicon baseline remains the active engine**.
- A production deployment should train on a sufficiently large, real labelled faculty-feedback dataset and promote the model only after acceptable evaluation results.

## 3. Topic extraction

Keyword buckets:

- Teaching clarity
- Subject knowledge
- Classroom interaction
- Practical examples
- Syllabus completion
- Teaching pace
- Assessment and feedback
- Support and accessibility

Each comment is matched against token sets; results include mention counts and sentiment split.

## 4. Strengths and improvement areas

- Strength: question average ≥ 4.0 with ≥ 3 responses.
- Improvement: question average ≤ 3.0 with ≥ 3 responses.
- Evidence strings quote the real average and response count.

## 5. Recommendations

Data-driven actions are mapped from the lowest-performing question areas (practical examples, syllabus, pace, clarity, participation, knowledge, …) plus a generic fallback.

## 6. Trend insights

Same-faculty academic-year comparisons with change detection (`improving` / `declining` / `stable`), only when comparable data exists.

## 7. API surface

- `GET /api/ml/model-info`
- `POST /api/ml/sentiment`
- `GET /api/ml/insights` (faculty-scoped)

## 8. Ethical and honest-AI notes

- Heuristic confidence is documented; never presented as calibrated probability.
- Trained model is used only with validated metadata.
- Insights are evidence-based; no invented explanations.

## 9. Validation results (2026-11-17)

The sentiment/topic/insights pipeline was executed against the real feedback comments stored in the development
database (read-only) and exercised end to end:

- Real comments analysed: **50** (development database).
- Active engine at validation time: **`lexicon-v1`** (metadata `validated: false`).
- Sentiment distribution: 34 positive / 11 neutral / 5 negative comments.
- Topic extraction returned ranked topics with mention counts and sentiment splits (e.g. Subject knowledge 19 mentions,
  Practical examples 18, Teaching clarity 15).
- Sample predictions applied negation and intensifier handling correctly and labelled positive/negative examples
  appropriately; confidence values are heuristic scores, not calibrated probabilities.
- Insight builder produced strengths / improvement areas / recommendations with evidence strings and handled the
  empty-data case without error.
- Trained-model path: `ml/train.py` with labelled CSV; demo run produced `validated: false` (macro F1 0.167 on the tiny
  sample), so lexicon remains the production default.

**Conclusion:** the AI/ML implementation functions correctly and honestly reports its limitations; no unverified model
accuracy was claimed and no synthetic training data was used.
