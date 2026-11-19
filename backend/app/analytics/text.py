"""Transparent, explainable NLP utilities used by the analytics API.

The production default is a lexicon baseline. It is not presented as a
statistically evaluated ML model. An optional TF-IDF classifier can be trained
from a real labelled dataset with ``ml/train.py``; it is only used when its
metadata records a completed evaluation.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

from app.core.config import PROJECT_DIR


TOKEN_RE = re.compile(r"[a-z][a-z']+")
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "can", "could",
    "did", "do", "does", "for", "from", "had", "has", "have", "he", "her", "his",
    "how", "i", "if", "in", "into", "is", "it", "its", "just", "me", "more", "most",
    "my", "no", "not", "of", "on", "or", "our", "out", "she", "should", "so", "some",
    "such", "than", "that", "the", "their", "them", "then", "there", "these", "they",
    "this", "those", "to", "too", "very", "was", "we", "were", "what", "when", "where",
    "which", "while", "who", "will", "with", "would", "you", "your", "also", "about",
    "after", "before", "because", "been", "being", "both", "each", "few", "over",
    "under", "again", "once", "here", "all", "any", "own", "same", "only", "other",
}

POSITIVE_WORDS = {
    "amazing", "awesome", "best", "better", "brilliant", "clear", "clearly", "comfortable",
    "committed", "confident", "cooperative", "creative", "dedicated", "effective",
    "encouraging", "engaging", "enjoyable", "excellent", "exceptional", "fantastic",
    "friendly", "good", "great", "helpful", "honest", "impressive", "informative",
    "inspiring", "interactive", "interesting", "kind", "knowledgeable", "learnt",
    "learned", "lovely", "motivating", "nice", "organized", "patient", "perfect",
    "practical", "professional", "punctual", "recommend", "relevant", "responsive",
    "satisfied", "smart", "strong", "supportive", "systematic", "thank", "thanks",
    "thorough", "useful", "valuable", "wonderful", "well", "understand", "understood",
    "easy", "simple", "beneficial", "clarifies", "clarified", "explains", "explained",
    "help", "helps", "helped", "improved", "improvement", "appreciate", "appreciated",
}

NEGATIVE_WORDS = {
    "angry", "annoying", "awful", "bad", "bias", "biased", "boring", "broken",
    "careless", "confusing", "confused", "difficult", "disappointed", "disappointing",
    "disorganized", "dull", "error", "errors", "fail", "failed", "fast", "hard",
    "harsh", "hate", "ignored", "incomplete", "ineffective", "insufficient", "late",
    "lazy", "lengthy", "loud", "messy", "misleading", "missing", "monotonous", "negative",
    "noisy", "not", "poor", "problem", "problems", "rude", "rushed", "slow", "strict",
    "struggle", "struggled", "terrible", "unclear", "unfair", "unhelpful", "unhappy",
    "uninteresting", "unnecessary", "unprofessional", "unresponsive", "unsatisfied",
    "unsupported", "weak", "worse", "worst", "wrong", "lack", "lacks", "lacking",
    "difficulty", "difficulties", "bored", "distracted", "delay", "delayed", "cancelled",
}

NEGATIONS = {"not", "no", "never", "neither", "nor", "hardly", "barely", "cannot", "can't", "don't", "didn't", "isn't", "wasn't", "won't", "wouldn't"}
INTENSIFIERS = {"very": 1.35, "really": 1.3, "extremely": 1.5, "highly": 1.4, "too": 1.2, "quite": 1.1, "so": 1.1}

TOPIC_KEYWORDS: dict[str, set[str]] = {
    "Teaching clarity": {"clear", "clarity", "explain", "explains", "explained", "explanation", "understand", "understood", "simple", "confusing", "unclear", "concept", "concepts"},
    "Subject knowledge": {"knowledge", "knowledgeable", "subject", "expert", "command", "doubt", "doubts", "answer", "answers", "deep"},
    "Classroom interaction": {"interactive", "interaction", "participate", "participation", "engage", "engaging", "discussion", "questions", "asks", "listen", "listens"},
    "Practical examples": {"practical", "example", "examples", "real", "industry", "application", "applications", "hands", "demo", "demonstration", "case"},
    "Syllabus completion": {"syllabus", "complete", "completed", "coverage", "portions", "finish", "finished", "late", "incomplete", "planned"},
    "Teaching pace": {"pace", "fast", "slow", "rushed", "speed", "hurry", "lengthy", "time"},
    "Assessment and feedback": {"exam", "marks", "assignment", "assignments", "test", "tests", "grading", "evaluation", "feedback", "correction"},
    "Support and accessibility": {"support", "supportive", "help", "helpful", "doubt", "accessible", "available", "response", "responsive", "approachable"},
}


def clean_text(text: str) -> str:
    text = text.lower().replace("’", "'")
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = re.sub(r"[^a-z'\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str, *, remove_stopwords: bool = True) -> list[str]:
    tokens = TOKEN_RE.findall(clean_text(text))
    if remove_stopwords:
        tokens = [token for token in tokens if token not in STOPWORDS]
    return tokens


def preprocess_text(text: str) -> str:
    tokens = tokenize(text, remove_stopwords=True)
    return " ".join(tokens)


def _word_score(word: str) -> int:
    if word in POSITIVE_WORDS:
        return 1
    if word in NEGATIVE_WORDS:
        return -1
    return 0


def analyze_sentiment(text: str) -> dict[str, Any]:
    """Return an explainable heuristic sentiment label.

    ``confidence`` is a heuristic strength score, not a calibrated probability.
    """
    raw_tokens = TOKEN_RE.findall(clean_text(text))
    score = 0.0
    matched: list[str] = []
    for index, token in enumerate(raw_tokens):
        base = _word_score(token)
        if base == 0:
            continue
        multiplier = 1.0
        if index > 0 and raw_tokens[index - 1] in INTENSIFIERS:
            multiplier *= INTENSIFIERS[raw_tokens[index - 1]]
        window = raw_tokens[max(0, index - 3):index]
        if any(negation in window for negation in NEGATIONS):
            base *= -1
            matched.append(f"not {token}")
        else:
            matched.append(token)
        score += base * multiplier

    token_count = max(len(raw_tokens), 1)
    if score > 0.2:
        label = "positive"
    elif score < -0.2:
        label = "negative"
    else:
        label = "neutral"
    strength = min(1.0, abs(score) / max(2.0, token_count * 0.35))
    confidence = round(0.5 + 0.45 * strength, 3) if label != "neutral" else 0.55
    return {
        "label": label,
        "score": round(score, 3),
        "confidence": confidence,
        "matched_terms": matched[:8],
        "method": "lexicon-v1",
        "limitations": "Heuristic lexicon baseline. Not a validated ML probability.",
    }


def extract_keywords(comments: list[str], top_k: int = 15) -> list[dict[str, Any]]:
    """Extract frequent unigrams and bigrams without a heavy runtime dependency.

    TF-IDF is used by the optional offline training pipeline (``ml/train.py``).
    The API keeps this path lightweight so the first analytics request is fast.
    """
    if not comments:
        return []
    unigrams: Counter[str] = Counter()
    bigrams: Counter[str] = Counter()
    for comment in comments:
        tokens = tokenize(comment)
        unigrams.update(tokens)
        bigrams.update(" ".join(pair) for pair in zip(tokens, tokens[1:]))
    combined: Counter[str] = Counter()
    for term, count in unigrams.items():
        combined[term] += count * 1.0
    for term, count in bigrams.items():
        combined[term] += count * 1.4
    return [
        {"keyword": keyword, "weight": round(float(score), 2)}
        for keyword, score in combined.most_common(top_k)
    ]


def classify_topics(comments: list[str]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, int]] = defaultdict(
        lambda: {"mentions": 0, "positive": 0, "neutral": 0, "negative": 0, "evidence": 0}
    )
    for comment in comments:
        tokens = set(tokenize(comment))
        sentiment = analyze_sentiment(comment)
        for topic, keywords in TOPIC_KEYWORDS.items():
            if tokens & keywords:
                buckets[topic]["mentions"] += 1
                buckets[topic]["evidence"] += 1
                buckets[topic][sentiment["label"]] += 1
    result = [{"topic": topic, **values} for topic, values in buckets.items()]
    return sorted(result, key=lambda item: (-item["mentions"], item["topic"]))


def analyze_comments(comments: Iterable[str]) -> dict[str, Any]:
    comment_list = [comment for comment in comments if comment and comment.strip()]
    analyses = [analyze_sentiment(comment) for comment in comment_list]
    counts = Counter(item["label"] for item in analyses)
    total = len(analyses)
    return {
        "total_comments": total,
        "positive": counts.get("positive", 0),
        "neutral": counts.get("neutral", 0),
        "negative": counts.get("negative", 0),
        "positive_pct": round(100 * counts.get("positive", 0) / total, 1) if total else 0.0,
        "neutral_pct": round(100 * counts.get("neutral", 0) / total, 1) if total else 0.0,
        "negative_pct": round(100 * counts.get("negative", 0) / total, 1) if total else 0.0,
        "method": sentiment_engine_info()["active_engine"],
        "limitations": sentiment_engine_info()["limitations"],
    }


@lru_cache(maxsize=1)
def _load_trained_model() -> tuple[Any, Any, dict[str, Any]] | None:
    model_path = PROJECT_DIR / "ml" / "models" / "sentiment_model.joblib"
    metadata_path = PROJECT_DIR / "ml" / "models" / "sentiment_model_metadata.json"
    if not model_path.exists() or not metadata_path.exists():
        return None
    try:
        import joblib

        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if not metadata.get("validated", False):
            return None
        bundle = joblib.load(model_path)
        return bundle["vectorizer"], bundle["model"], metadata
    except Exception:
        return None


def sentiment_engine_info() -> dict[str, Any]:
    loaded = _load_trained_model()
    if loaded is not None:
        _, _, metadata = loaded
        return {
            "active_engine": "tfidf-classifier",
            "validated": True,
            "metrics": metadata.get("metrics", {}),
            "trained_at": metadata.get("trained_at"),
            "limitations": "Trained on the supplied labelled dataset. Review its scope and class balance before relying on predictions.",
        }
    return {
        "active_engine": "lexicon-v1",
        "validated": False,
        "metrics": {},
        "trained_at": None,
        "limitations": "Transparent rule-based lexicon baseline. It has not been evaluated as a statistical ML model.",
    }


def predict_sentiment(text: str) -> dict[str, Any]:
    loaded = _load_trained_model()
    if loaded is None:
        return analyze_sentiment(text)
    vectorizer, model, _ = loaded
    cleaned = preprocess_text(text)
    prediction = str(model.predict([cleaned])[0])
    result = analyze_sentiment(text)
    result.update(
        {
            "label": prediction,
            "method": "tfidf-classifier",
            "limitations": "Prediction from a trained TF-IDF classifier. Not calibrated unless documented in model metadata.",
        }
    )
    if hasattr(model, "predict_proba"):
        try:
            probabilities = model.predict_proba([cleaned])[0]
            result["confidence"] = round(float(max(probabilities)), 3)
        except Exception:
            pass
    return result
