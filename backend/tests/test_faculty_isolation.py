"""Critical security test: one faculty member can never see another's feedback."""

from __future__ import annotations

from fastapi.testclient import TestClient

from .conftest import ratings, submit_feedback

ALPHA_COMMENT = "Alpha explains every concept clearly and gives helpful worked examples."
BETA_COMMENT = "Beta lectures were confusing and the notes were incomplete and rushed."


def _seed_two_faculty_feedback(client: TestClient, data: dict, student_headers: dict) -> None:
    submit_feedback(
        client, data, student_headers, offering_key="a", score=5, comment=ALPHA_COMMENT
    )
    submit_feedback(
        client, data, student_headers, offering_key="b", score=1, comment=BETA_COMMENT
    )


def test_each_faculty_sees_only_their_own_feedback(
    client: TestClient, data: dict, student_headers: dict, faculty_a_headers: dict, faculty_b_headers: dict
) -> None:
    _seed_two_faculty_feedback(client, data, student_headers)

    alpha = client.get("/api/faculty/me/dashboard", headers=faculty_a_headers)
    assert alpha.status_code == 200, alpha.text
    alpha_body = alpha.json()
    assert alpha_body["faculty_id"] == data["faculty"]["a"]
    assert alpha_body["overall"]["response_count"] == 1
    assert alpha_body["overall"]["average_rating"] == 5.0
    assert {row["subject_code"] for row in alpha_body["comments"]} == {"CS501", "CS503"} or {
        row["subject_code"] for row in alpha_body["comments"]
    } == {"CS501"}
    assert ALPHA_COMMENT in {row["comment"] for row in alpha_body["comments"]}
    assert BETA_COMMENT not in {row["comment"] for row in alpha_body["comments"]}

    beta = client.get("/api/faculty/me/dashboard", headers=faculty_b_headers)
    assert beta.status_code == 200, beta.text
    beta_body = beta.json()
    assert beta_body["faculty_id"] == data["faculty"]["b"]
    assert beta_body["overall"]["response_count"] == 1
    assert beta_body["overall"]["average_rating"] == 1.0
    assert {row["subject_code"] for row in beta_body["comments"]} == {"CS502"}
    assert BETA_COMMENT in {row["comment"] for row in beta_body["comments"]}
    assert ALPHA_COMMENT not in {row["comment"] for row in beta_body["comments"]}


def test_filters_cannot_cross_the_faculty_boundary(
    client: TestClient, data: dict, student_headers: dict, faculty_a_headers: dict
) -> None:
    _seed_two_faculty_feedback(client, data, student_headers)

    # Faculty A explicitly asks for Faculty B's subject. The JWT scope still wins,
    # so the result must be empty rather than leaking B's data.
    response = client.get(
        "/api/faculty/me/dashboard", headers=faculty_a_headers, params={"subject_code": "CS502"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["overall"]["response_count"] == 0
    assert body["comments"] == []
    assert all(row["response_count"] == 0 for row in body["question_stats"])


def test_comments_endpoint_is_scoped(
    client: TestClient, data: dict, student_headers: dict, faculty_a_headers: dict
) -> None:
    _seed_two_faculty_feedback(client, data, student_headers)
    response = client.get("/api/faculty/me/comments", headers=faculty_a_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["comment"] == ALPHA_COMMENT


def test_student_identifiers_are_never_returned_to_faculty(
    client: TestClient, data: dict, student_headers: dict, faculty_a_headers: dict
) -> None:
    _seed_two_faculty_feedback(client, data, student_headers)
    raw = client.get("/api/faculty/me/dashboard", headers=faculty_a_headers).text
    assert data["student_id"] not in raw
    assert data["second_student_id"] not in raw
    assert "student_id" not in raw


def test_role_boundaries_are_enforced(
    client: TestClient, data: dict, faculty_a_headers: dict, student_headers: dict, admin_headers: dict
) -> None:
    # Faculty cannot reach admin-only analytics.
    assert client.get("/api/analytics/admin", headers=faculty_a_headers).status_code == 403
    # Students cannot reach faculty endpoints.
    assert client.get("/api/faculty/me/dashboard", headers=student_headers).status_code == 403
    # Faculty cannot reach student endpoints.
    assert client.get("/api/students/me/dashboard", headers=faculty_a_headers).status_code == 403
    # Anonymous requests are rejected.
    assert client.get("/api/faculty/me/dashboard").status_code == 401
    # Admin can use the admin analytics entry point.
    assert client.get("/api/analytics/admin", headers=admin_headers).status_code == 200


def test_admin_can_view_each_faculty_separately(
    client: TestClient, data: dict, student_headers: dict, admin_headers: dict
) -> None:
    _seed_two_faculty_feedback(client, data, student_headers)

    alpha = client.get(
        f"/api/analytics/admin/faculty/{data['faculty']['a']}", headers=admin_headers
    )
    beta = client.get(
        f"/api/analytics/admin/faculty/{data['faculty']['b']}", headers=admin_headers
    )
    assert alpha.status_code == beta.status_code == 200
    assert alpha.json()["overall"]["average_rating"] == 5.0
    assert beta.json()["overall"]["average_rating"] == 1.0
    assert BETA_COMMENT not in {row["comment"] for row in alpha.json()["comments"]}
