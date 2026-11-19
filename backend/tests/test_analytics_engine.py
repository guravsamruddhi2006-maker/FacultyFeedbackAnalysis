"""Reusable analytics engine tests (Pandas / NumPy based calculations)."""

from __future__ import annotations

import math

from app.analytics.engine import (
    average,
    create_rating_histogram,
    overall_average,
    participation_rate,
    question_statistics,
    rating_distribution,
    year_comparison,
)


def _answers(*ratings: int) -> list[dict[str, int]]:
    return [{"question_id": 1, "rating": rating} for rating in ratings]


def test_average_handles_empty_and_partial_input() -> None:
    assert average([]) == 0.0
    assert average([1, 2, 3, 4, 5]) == 3.0
    assert average([5, 5, 5]) == 5.0


def test_overall_average_is_mean_of_ratings() -> None:
    assert overall_average([4, 5, 3]) == 4.0
    assert overall_average([5, 5, 5, 5]) == 5.0
    assert math.isclose(overall_average([2, 4]), 3.0)


def test_question_statistics_group_and_average() -> None:
    stats = question_statistics(
        [
            {"question_id": 2, "rating": 4},
            {"question_id": 2, "rating": 5},
            {"question_id": 1, "rating": 3},
        ]
    )
    assert {item["question_id"]: item for item in stats}[1]["average_rating"] == 3.0
    assert {item["question_id"]: item for item in stats}[2]["average_rating"] == 4.5


def test_rating_distribution_counts_and_percentages() -> None:
    distribution = rating_distribution(_answers(5, 4, 5, 5))
    by_rating = {item["rating"]: item for item in distribution}
    assert by_rating[5]["count"] == 3
    assert by_rating[4]["count"] == 1
    assert by_rating[5]["percentage"] == 75.0


def test_year_comparison_sorts_by_year() -> None:
    rows = year_comparison(
        [
            {"academic_year": "2027-28", "ratings": [5, 4]},
            {"academic_year": "2026-27", "ratings": [3, 3, 3]},
        ]
    )
    assert [row["academic_year"] for row in rows] == ["2026-27", "2027-28"]
    assert rows[-1]["average_rating"] == 4.5


def test_participation_rate_is_percentage_of_expected_responses() -> None:
    assert participation_rate(2, 10) == 20.0
    assert participation_rate(5, 10) == 50.0
    assert participation_rate(0, 0) == 0.0


def test_histogram_renders_without_error() -> None:
    distribution = [
        {"rating": 5, "label": "Excellent", "count": 3, "percentage": 60.0},
        {"rating": 3, "label": "Average", "count": 2, "percentage": 40.0},
    ]
    figure = create_rating_histogram(distribution)
    assert figure is not None
    import matplotlib.pyplot as plt

    plt.close(figure)
