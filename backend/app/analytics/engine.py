"""Reusable analytics engine built on Pandas and NumPy.

The API layer keeps its SQL aggregations, but every calculation required by
the dashboards, insights and exports has a single reusable implementation here
so that reports, tests and future endpoints cannot drift apart.

All functions accept plain Python collections and return plain JSON-ready
dictionaries (or a Matplotlib figure for chart export).
"""

from __future__ import annotations

from typing import Any, Iterable, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def average(values: Iterable[float]) -> float:
    numbers = [float(value) for value in values if value is not None]
    if not numbers:
        return 0.0
    return float(round(float(np.mean(np.asarray(numbers, dtype=float))), 2))


def overall_average(ratings: Sequence[int]) -> float:
    return average(ratings)


def question_statistics(answers: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    frame = pd.DataFrame(
        [
            {"question_id": int(item["question_id"]), "rating": int(item["rating"])}
            for item in answers
            if item.get("rating") is not None
        ]
    )
    if frame.empty:
        return []
    grouped = frame.groupby("question_id")["rating"].agg(["mean", "count"])
    return [
        {
            "question_id": int(row.name),
            "average_rating": round(float(row["mean"]), 2),
            "response_count": int(row["count"]),
        }
        for _, row in grouped.iterrows()
    ]


def rating_distribution(answers: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    frame = pd.DataFrame(
        [
            {"rating": int(item["rating"])}
            for item in answers
            if item.get("rating") is not None
        ]
    )
    labels = {1: "Very Poor", 2: "Poor", 3: "Average", 4: "Good", 5: "Excellent"}
    if frame.empty:
        return [
            {"rating": rating, "label": labels[rating], "count": 0, "percentage": 0.0}
            for rating in range(1, 6)
        ]
    counts = frame["rating"].value_counts().to_dict()
    total = int(len(frame))
    return [
        {
            "rating": rating,
            "label": labels[rating],
            "count": int(counts.get(rating, 0)),
            "percentage": round(100 * int(counts.get(rating, 0)) / total, 1) if total else 0.0,
        }
        for rating in range(1, 6)
    ]


def year_comparison(groups: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """groups: list of {academic_year, ratings: [int, ...]}"""
    rows = []
    for group in groups:
        rows.append(
            {
                "academic_year": group.get("academic_year"),
                "average_rating": average(group.get("ratings") or []),
                "response_count": len(group.get("ratings") or []),
            }
        )
    return sorted(rows, key=lambda row: str(row.get("academic_year") or ""))


def participation_rate(feedback_count: int, expected_responses: int) -> float:
    denominator = max(int(expected_responses), 1)
    return round(100 * int(feedback_count) / denominator, 1)


def create_rating_histogram(distribution: Sequence[dict[str, Any]]) -> matplotlib.figure.Figure:
    fig, axis = plt.subplots(figsize=(6, 4))
    labels = [row["label"] for row in distribution]
    counts = [int(row["count"]) for row in distribution]
    axis.bar(labels, counts, color="#2563eb")
    axis.set_ylim(0, max([int(row["count"]) for row in distribution], default=0) * 1.15 or 1)
    axis.set_ylabel("Responses")
    axis.set_title("Rating distribution")
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    fig.tight_layout()
    return fig
