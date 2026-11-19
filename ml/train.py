"""FacultyInsight AI — sentiment model training entry point.

Trains a TF-IDF + scikit-learn classifier on a real labelled CSV dataset and
persists the model plus an evaluation metadata document.

Usage:
    python ml/train.py --data ml/data/sentiment_labeled.csv

The application only activates the trained model when the metadata file
records a completed, validated evaluation. Without a labelled dataset the
service falls back to the transparent lexicon baseline and reports that state.

This script never writes a validated model from synthetic data.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import ConfusionMatrixDisplay, classification_report, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

LABELS = ["positive", "neutral", "negative"]


def load_dataset(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = {"text", "label"}
    if not required.issubset(set(frame.columns)):
        raise ValueError(f"Labelled dataset must contain columns: {sorted(required)}")
    frame["text"] = frame["text"].astype(str).str.strip()
    frame["label"] = frame["label"].astype(str).str.strip().str.lower()
    frame = frame[frame["text"].map(lambda value: len(value) > 0) & frame["label"].isin(LABELS)].reset_index(drop=True)
    if len(frame) == 0:
        raise ValueError("Labelled dataset is empty after validation.")
    counts = frame["label"].value_counts().to_dict()
    if any(count < 2 for count in counts.values()):
        raise ValueError("Each sentiment label needs at least two samples to train and evaluate.")
    return frame


def train(frame: pd.DataFrame, test_size: float = 0.25, seed: int = 42) -> dict[str, Any]:
    encoder = LabelEncoder()
    frame["target"] = encoder.fit_transform(frame["label"])
    x_train, x_test, y_train, y_test = train_test_split(
        frame["text"],
        frame["target"],
        test_size=test_size,
        random_state=seed,
        stratify=frame["target"],
    )
    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer(stop_words="english", max_features=5000)),
            ("clf", None),
        ]
    )
    from sklearn.linear_model import LogisticRegression

    pipeline.set_params(clf=LogisticRegression(max_iter=2000, random_state=seed))
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    probabilities = pipeline.predict_proba(x_test)

    matrix = confusion_matrix(y_test, predictions)
    report = classification_report(
        y_test,
        predictions,
        target_names=encoder.classes_.tolist(),
        output_dict=True,
    )
    metrics = {
        "accuracy": round(float(report["accuracy"]), 4),
        "macro_f1": round(float(f1_score(y_test, predictions, average="macro")), 4),
        "precision_macro": round(float(precision_score(y_test, predictions, average="macro")), 4),
        "recall_macro": round(float(recall_score(y_test, predictions, average="macro")), 4),
        "confusion_matrix": {
            "labels": encoder.classes_.tolist(),
            "matrix": [[int(value) for value in row] for row in matrix],
        },
        "classification_report": report,
        "trained_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "training_samples": int(len(x_train)),
        "test_samples": int(len(x_test)),
        "training_labels": frame["label"].value_counts().to_dict(),
        "notes": "Metrics are computed on a held-out stratified split. This is an evaluation of the trained model, not a guarantee of real-world performance.",
    }
    bundle = {"vectorizer": pipeline.named_steps["tfidf"], "model": pipeline.named_steps["clf"], "encoder": encoder}
    return {"bundle": bundle, "metrics": metrics, "model_name": "tfidf-logistic-regression-sentiment-v1"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the FacultyInsight AI sentiment model.")
    parser.add_argument("--data", default="ml/data/sentiment_labeled.csv", help="Path to the labelled CSV (columns: text,label)")
    parser.add_argument("--model-out", default="ml/models/sentiment_model.joblib")
    parser.add_argument("--metadata-out", default="ml/models/sentiment_model_metadata.json")
    args = parser.parse_args()

    dataset = load_dataset(Path(args.data))
    result = train(dataset)
    model_path = Path(args.model_out)
    metadata_path = Path(args.metadata_out)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(result["bundle"], model_path)
    metadata = {
        "validated": bool(result["metrics"].get("macro_f1", 0) >= 0.5),
        "model_name": result["model_name"],
        "labels": LABELS,
        "metrics": result["metrics"],
        "trained_at": result["metrics"]["trained_at"],
        "training_script": "ml/train.py",
        "notes": result["metrics"]["notes"],
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Trained sentiment model written to {model_path}")
    print(json.dumps(result["metrics"], indent=2, default=str))


if __name__ == "__main__":
    main()
