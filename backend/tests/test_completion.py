"""Completion tracking, roster authorization and anonymity guarantees."""

from __future__ import annotations

from fastapi.testclient import TestClient

from .conftest import submit_feedback

SCOPE = {
    "subject_code": "CS501",
    "academic_year": "2026-27",
    "semester_number": 5,
}


def _enroll(db, student_ids: list[str], **overrides) -> None:
    scope = {**SCOPE, **overrides}
    with db.transaction():
        with db.cursor() as cur:
            for student_id in student_ids:
                cur.execute(
                    """
                    INSERT INTO student_enrollments
                        (student_id, subject_code, academic_year, semester_number)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        student_id,
                        scope["subject_code"],
                        scope["academic_year"],
                        scope["semester_number"],
                    ),
                )


def _completion(client: TestClient, headers: dict, **overrides):
    return client.get(
        "/api/faculty/me/completion",
        headers=headers,
        params={**SCOPE, **overrides},
    )


def test_completion_without_roster_is_explicitly_unavailable(
    client: TestClient, data: dict, faculty_a_headers: dict
) -> None:
    response = _completion(client, faculty_a_headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["roster_available"] is False
    assert body["eligible_count"] == 0
    assert body["submitted_count"] == 0
    assert body["pending_count"] == 0
    assert body["pending_students"] == []
    assert "never reveals" in body["privacy_notice"]


def test_completion_counts_only_verified_roster_and_keeps_feedback_anonymous(
    client: TestClient,
    db,
    data: dict,
    faculty_a_headers: dict,
    student_headers: dict,
) -> None:
    _enroll(db, [data["student_id"], data["second_student_id"]])
    submit_feedback(
        client,
        data,
        student_headers,
        offering_key="a",
        score=5,
        comment="The private comment must never appear in a completion response.",
    )

    response = _completion(client, faculty_a_headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["roster_available"] is True
    assert body["eligible_count"] == 2
    assert body["submitted_count"] == 1
    assert body["pending_count"] == 1
    assert body["completion_percentage"] == 50.0
    assert [row["student_id"] for row in body["pending_students"]] == [data["second_student_id"]]
    # The response must not leak the submitted student, feedback content or IDs.
    assert data["student_id"] not in response.text
    assert "private comment" not in response.text
    assert "feedback_id" not in response.text
    assert "comment" not in body


def test_completion_ignores_feedback_from_students_outside_the_roster(
    client: TestClient,
    db,
    data: dict,
    faculty_a_headers: dict,
    student_headers: dict,
) -> None:
    _enroll(db, [data["second_student_id"]])
    submit_feedback(client, data, student_headers, offering_key="a")

    body = _completion(client, faculty_a_headers).json()

    assert body["eligible_count"] == 1
    assert body["submitted_count"] == 0
    assert body["pending_count"] == 1
    assert body["completion_percentage"] == 0.0
    assert body["pending_students"][0]["student_id"] == data["second_student_id"]


def test_completion_is_limited_to_the_faculty_members_own_subjects(
    client: TestClient, data: dict, faculty_b_headers: dict
) -> None:
    # Faculty B teaches CS502, not CS501.
    response = _completion(client, faculty_b_headers)
    assert response.status_code == 404
    assert "No active subject selection" in response.json()["detail"]

    response = _completion(client, faculty_b_headers, subject_code="CS502")
    assert response.status_code == 200
    assert response.json()["subject_code"] == "CS502"


def test_students_cannot_read_completion(
    client: TestClient, data: dict, student_headers: dict
) -> None:
    response = _completion(client, student_headers)
    assert response.status_code == 403


def test_completion_pdf_contains_pending_students_and_requires_a_roster(
    client: TestClient,
    db,
    data: dict,
    faculty_a_headers: dict,
    student_headers: dict,
) -> None:
    submit_feedback(client, data, student_headers, offering_key="a")

    no_roster = client.get(
        "/api/reports/faculty/me/completion",
        headers=faculty_a_headers,
        params={**SCOPE, "format": "pdf"},
    )
    assert no_roster.status_code == 409
    assert "verified class roster" in no_roster.json()["detail"]

    _enroll(db, [data["student_id"], data["second_student_id"]])
    response = client.get(
        "/api/reports/faculty/me/completion",
        headers=faculty_a_headers,
        params={**SCOPE, "format": "pdf"},
    )
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/pdf")
    assert "attachment" in response.headers["content-disposition"]
    assert "feedback-completion-CS501" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF")


def test_admin_manages_the_verified_roster(
    client: TestClient, data: dict, admin_headers: dict
) -> None:
    bulk = client.post(
        "/api/admin/enrollments/bulk",
        headers=admin_headers,
        json={
            **SCOPE,
            "student_ids": [data["student_id"], data["second_student_id"], "UNKNOWN1"],
        },
    )
    assert bulk.status_code == 201, bulk.text
    assert bulk.json()["added_count"] == 2
    assert bulk.json()["unknown"] == ["UNKNOWN1"]

    listing = client.get("/api/admin/enrollments", headers=admin_headers, params=SCOPE)
    assert listing.status_code == 200, listing.text
    assert listing.json()["total"] == 2
    assert listing.json()["scope"]["subject_name"] == "Data Structures"

    duplicate = client.post(
        "/api/admin/enrollments",
        headers=admin_headers,
        json={**SCOPE, "student_id": data["student_id"]},
    )
    assert duplicate.status_code == 201
    assert duplicate.json()["created"] is False

    enrollment_id = listing.json()["items"][0]["enrollment_id"]
    removed = client.delete(f"/api/admin/enrollments/{enrollment_id}", headers=admin_headers)
    assert removed.status_code == 200
    assert "Feedback was not changed" in removed.json()["message"]

    after = client.get("/api/admin/enrollments", headers=admin_headers, params=SCOPE)
    assert after.json()["total"] == 1

    audit = client.get(
        "/api/admin/audit-logs",
        headers=admin_headers,
        params={"action": "student_enrollment.bulk_add"},
    )
    assert audit.status_code == 200
    assert audit.json()["total"] >= 1


def test_admin_cannot_enroll_an_archived_student(
    client: TestClient, data: dict, admin_headers: dict
) -> None:
    archived = client.patch(
        f"/api/admin/students/{data['second_student_id']}/status",
        headers=admin_headers,
        json={"is_active": False},
    )
    assert archived.status_code == 200, archived.text

    response = client.post(
        "/api/admin/enrollments",
        headers=admin_headers,
        json={**SCOPE, "student_id": data["second_student_id"]},
    )
    assert response.status_code == 400
    assert "archived" in response.json()["detail"]


def test_roster_scope_must_match_the_catalog_semester(
    client: TestClient, data: dict, admin_headers: dict
) -> None:
    response = client.post(
        "/api/admin/enrollments",
        headers=admin_headers,
        json={
            "student_id": data["student_id"],
            "subject_code": "CS501",
            "academic_year": "2026-27",
            "semester_number": 6,
        },
    )
    assert response.status_code == 400
    assert "belongs to semester 5" in response.json()["detail"]
