"""AI insight generation tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from .conftest import TEST_PASSWORD_HASH, bearer, ratings, submit_feedback


def test_ml_insights_requires_authentication(client: TestClient) -> None:
    assert client.get("/api/ml/insights").status_code == 401


def test_ml_insights_requires_faculty_role(client: TestClient, student_headers: dict) -> None:
    assert client.get("/api/ml/insights", headers=student_headers).status_code == 403


def test_faculty_ml_insights_include_evidence_and_recommendations(
    client: TestClient, data: dict, db, student_headers: dict, faculty_a_headers: dict
) -> None:
    submit_feedback(client, data, student_headers, offering_key="a", score=2, comment="The pace was too fast and the examples were missing.")
    second_headers = bearer(data["second_student_id"], "student")
    submit_feedback(client, data, second_headers, offering_key="a", score=2, comment="The syllabus coverage was incomplete.")

    third_headers = bearer("4UB26CS003", "student")
    with db.transaction():
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO students (student_id, name, department_id, password_hash) VALUES (%s, %s, %s, %s)",
                ("4UB26CS003", "Third Student", data["department_id"], TEST_PASSWORD_HASH),
            )

    submit_feedback(client, data, third_headers, offering_key="a", score=2, comment="The examples were missing from the lectures.")

    response = client.get("/api/ml/insights", headers=faculty_a_headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["faculty_id"] == data["faculty"]["a"]
    assert body["response_count"] == 3
    assert body["recommendations"], "Expected at least one evidence-based recommendation."
    for recommendation in body["recommendations"]:
        assert "recommendation" in recommendation
        assert "rationale" in recommendation
        assert "response_count" in recommendation

    insights = client.get("/api/faculty/me/dashboard", headers=faculty_a_headers).json()
    assert "insights" in insights
    assert insights["insights"]["methodology"]["evidence_required"] is True


def test_faculty_dashboard_includes_strengths_and_improvements(
    client: TestClient, data: dict, db, student_headers: dict, faculty_a_headers: dict
) -> None:
    submit_feedback(client, data, student_headers, offering_key="a", score=5, comment="Excellent teaching with clear concepts and helpful examples.")
    second_headers = bearer(data["second_student_id"], "student")
    submit_feedback(client, data, second_headers, offering_key="a", score=5, comment="Excellent teaching with clear concepts and helpful examples.")

    third_headers = bearer("4UB26CS003", "student")
    with db.transaction():
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO students (student_id, name, department_id, password_hash) VALUES (%s, %s, %s, %s)",
                ("4UB26CS003", "Third Student", data["department_id"], TEST_PASSWORD_HASH),
            )
    submit_feedback(client, data, third_headers, offering_key="a", score=5, comment="Excellent teaching with clear concepts and helpful examples.")

    body = client.get("/api/faculty/me/dashboard", headers=faculty_a_headers).json()
    assert body["strengths"]
    assert body["improvement_areas"] == []
    assert isinstance(body["trend_insights"], list)


def test_admin_faculty_view_includes_insights(
    client: TestClient, data: dict, student_headers: dict, admin_headers: dict
) -> None:
    submit_feedback(client, data, student_headers, offering_key="a", score=4, comment="Good teaching and useful practical examples.")
    response = client.get(f"/api/analytics/admin/faculty/{data['faculty']['a']}", headers=admin_headers)
    assert response.status_code == 200, response.text
    assert response.json()["insights"]["response_count"] == 1
