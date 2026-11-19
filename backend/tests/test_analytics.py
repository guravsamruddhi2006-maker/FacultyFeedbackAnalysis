"""Analytics correctness and explainability guarantees."""

from __future__ import annotations

from fastapi.testclient import TestClient

from .conftest import TEST_PASSWORD_HASH, bearer, ratings


def _submit_for_three_students(client: TestClient, data: dict, headers: list[dict]) -> None:
    for headers_for_student in headers:
        response = client.post(
            "/api/students/me/feedback",
            headers=headers_for_student,
            json={
                "offering_id": data["offerings"]["a"],
                "ratings": ratings(data, 5),
                "comment": "Excellent, clear and helpful lectures with useful practical examples.",
            },
        )
        assert response.status_code == 201, response.text


def test_analytics_reflect_actual_ratings(
    client: TestClient, data: dict, db, student_headers: dict, faculty_a_headers: dict
) -> None:
    third_headers = bearer("4UB26CS003", "student")
    with db.transaction():
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO students (student_id, name, department_id, password_hash) VALUES (%s, %s, %s, %s)",
                ("4UB26CS003", "Third Student", data["department_id"], TEST_PASSWORD_HASH),
            )
    _submit_for_three_students(client, data, [student_headers, bearer(data["second_student_id"], "student"), third_headers])

    response = client.get("/api/faculty/me/dashboard", headers=faculty_a_headers)
    assert response.status_code == 200
    body = response.json()

    assert body["overall"] == {"average_rating": 5.0, "response_count": 3}
    assert all(item["average_rating"] == 5.0 for item in body["question_stats"])
    assert all(item["response_count"] == 3 for item in body["question_stats"])
    distribution = {item["rating"]: item for item in body["rating_distribution"]}
    assert distribution[5]["count"] == 15
    assert distribution[5]["percentage"] == 100.0
    assert all(distribution[rating]["count"] == 0 for rating in (1, 2, 3, 4))

    sentiment = body["sentiment"]["summary"]
    assert sentiment["total_comments"] == 3
    assert sentiment["positive"] == 3
    assert sentiment["method"] in {"lexicon-v1", "tfidf-classifier"}
    assert sentiment["limitations"]

    # Three identical high ratings are enough evidence for strengths, not
    # improvements. The evidence text must quote the real count.
    assert body["strengths"], "expected evidence-backed strengths"
    assert body["improvement_areas"] == []
    assert all("3 ratings" in item["evidence"] for item in body["strengths"])

    assert len(body["trend"]) >= 1
    assert body["trend"][-1]["average_rating"] == 5.0


def test_zero_feedback_faculty_still_gets_question_scaffold(
    client: TestClient, data: dict, admin_headers: dict
) -> None:
    response = client.get(
        f"/api/analytics/admin/faculty/{data['faculty']['b']}", headers=admin_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["overall"] == {"average_rating": 0.0, "response_count": 0}
    assert len(body["question_stats"]) == len(data["question_ids"])
    assert all(item["average_rating"] == 0.0 and item["response_count"] == 0 for item in body["question_stats"])


def test_admin_analytics_aggregates_real_data(
    client: TestClient, data: dict, student_headers: dict, admin_headers: dict
) -> None:
    for key in ("a", "b"):
        client.post(
            "/api/students/me/feedback",
            headers=student_headers,
            json={
                "offering_id": data["offerings"][key],
                "ratings": ratings(data, 3),
                "comment": "The classes were average and could use more practical demonstrations.",
            },
        )
    response = client.get("/api/analytics/admin", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["counts"]["feedback_count"] == 2
    assert body["counts"]["average_rating"] == 3.0
    assert body["submission_rate"] >= 0
    assert "coverage indicator" in body["submission_rate_note"]


def test_model_info_does_not_fabricate_accuracy(client: TestClient, student_headers: dict) -> None:
    response = client.get("/api/ml/model-info", headers=student_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["active_engine"] in {"lexicon-v1", "tfidf-classifier"}
    assert "note" in body and "limitations" in body
    if body["active_engine"] == "lexicon-v1":
        assert body["validated"] is False
        assert body["metrics"] == {}


def test_sentiment_endpoint_is_explainable(client: TestClient, student_headers: dict) -> None:
    response = client.post(
        "/api/ml/sentiment",
        headers=student_headers,
        json={"texts": [{"text": "The teacher was excellent and very helpful."}, {"text": "The lectures were confusing and rushed."}]},
    )
    assert response.status_code == 200
    results = response.json()["results"]
    assert results[0]["label"] == "positive"
    assert results[1]["label"] == "negative"
    for result in results:
        assert result["method"] in {"lexicon-v1", "tfidf-classifier"}
        assert "confidence" in result
