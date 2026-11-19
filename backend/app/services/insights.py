"""Evidence-based insight and improvement-recommendation generation.

Every insight produced here is derived from real aggregated feedback data
(rating averages, response counts and anonymised comment text). Nothing is
hardcoded and no rating change is explained without supporting numbers.
"""

from __future__ import annotations

from typing import Any

from app.analytics.text import analyze_comments, classify_topics

STRENGTH_THRESHOLD = 4.0
STRENGTH_MIN_RESPONSES = 3
IMPROVEMENT_THRESHOLD = 3.0
IMPROVEMENT_MIN_RESPONSES = 3

RECOMMENDATION_LIBRARY: list[tuple[str, str]] = [
    ("practical", "Include more real-world, hands-on examples and live demonstrations."),
    ("syllabus", "Review syllabus pacing and redistribute topics to protect coverage."),
    ("pace", "Adjust the teaching pace and schedule additional revision sessions."),
    ("clarity", "Increase concept-clarification opportunities such as worked examples and checks for understanding."),
    ("participation", "Add structured interactive activities and peer discussion slots."),
    ("knowledge", "Reinforce deeper subject knowledge through doubt-clearing sessions and advanced references."),
    ("example", "Include more practical examples and real-world case studies."),
]


def _recommendation_for(question_text: str, average_rating: float, response_count: int) -> dict[str, Any]:
    lowered = question_text.lower()
    for key, action in RECOMMENDATION_LIBRARY:
        if key in lowered or key in lowered.replace(" ", ""):
            rationale = (
                f"Reported by {response_count} student(s) with an average rating of {average_rating:.2f}/5."
            )
            return {
                "area": question_text.rstrip("."),
                "average_rating": average_rating,
                "response_count": response_count,
                "recommendation": action,
                "rationale": rationale,
                "evidence_level": "statistical",
                "threshold_met": True,
            }
    return {
        "area": question_text.rstrip("."),
        "average_rating": average_rating,
        "response_count": response_count,
        "recommendation": "Schedule a follow-up feedback cycle after pedagogical adjustments.",
        "rationale": f"Reported by {response_count} student(s) with an average rating of {average_rating:.2f}/5.",
        "evidence_level": "statistical",
        "threshold_met": True,
    }


def build_insights(
    *,
    question_rows: list[dict[str, Any]],
    comments: list[dict[str, Any]],
    overall_average: float = 0.0,
    response_count: int = 0,
) -> dict[str, Any]:
    strengths: list[dict[str, Any]] = []
    improvements: list[dict[str, Any]] = []
    recommendations: list[dict[str, Any]] = []

    for row in question_rows:
        count = int(row.get("response_count") or 0)
        average = float(row.get("average_rating") or 0.0)
        if count < STRENGTH_MIN_RESPONSES and count < IMPROVEMENT_MIN_RESPONSES:
            continue
        if average >= STRENGTH_THRESHOLD and count >= STRENGTH_MIN_RESPONSES:
            strengths.append(
                {
                    "area": row["question_text"].rstrip("."),
                    "average_rating": average,
                    "response_count": count,
                    "strength": True,
                }
            )
        elif average <= IMPROVEMENT_THRESHOLD and count >= IMPROVEMENT_MIN_RESPONSES:
            item = _recommendation_for(row["question_text"], average, count)
            improvements.append(
                {
                    "area": item["area"],
                    "average_rating": average,
                    "response_count": count,
                    "recommendation": item["recommendation"],
                }
            )
            recommendations.append(item)

    sentiment = analyze_comments([row["comment"] for row in comments if row.get("comment")])
    topics = classify_topics([row["comment"] for row in comments if row.get("comment")])

    return {
        "generated_at": None,
        "overall_average_rating": round(overall_average, 2),
        "response_count": response_count,
        "strengths": strengths,
        "improvement_areas": improvements,
        "recommendations": recommendations,
        "sentiment": {
            "summary": sentiment,
            "topics": topics,
        },
        "methodology": {
            "rating_averaging": "mean of 1..5 ratings with response counts",
            "strength_threshold": f"{STRENGTH_THRESHOLD} average with at least {STRENGTH_MIN_RESPONSES} responses",
            "improvement_threshold": f"{IMPROVEMENT_THRESHOLD} average with at least {IMPROVEMENT_MIN_RESPONSES} responses",
            "evidence_required": True,
        },
    }


def build_trend_insights(trend_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    insights: list[dict[str, Any]] = []
    rows = [row for row in trend_rows if row.get("academic_year") and row.get("response_count")]
    if len(rows) < 2:
        return insights
    ordered = sorted(rows, key=lambda row: row["academic_year"])
    previous = ordered[0]
    current = ordered[-1]
    delta = round(float(current["average_rating"]) - float(previous["average_rating"]), 2)
    direction = "improving" if delta > 0.05 else "declining" if delta < -0.05 else "stable"
    insights.append(
        {
            "academic_year": current["academic_year"],
            "previous_academic_year": previous["academic_year"],
            "average_rating": float(current["average_rating"]),
            "previous_average_rating": float(previous["average_rating"]),
            "change": delta,
            "direction": direction,
            "response_count": int(current["response_count"]),
            "evidence": f"{current['response_count']} responses in the latest period.",
            "generated_from": "real aggregated ratings only",
        }
    )
    return insights
