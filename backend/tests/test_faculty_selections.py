"""Faculty self-selection, subject requests and student visibility rules."""

from __future__ import annotations

import psycopg
from fastapi.testclient import TestClient

from .conftest import bearer, submit_feedback
from app.schema import _CORRECTION_SQL


def _create_subject(
    client: TestClient, admin_headers: dict, code: str, name: str, semester: int
) -> None:
    response = client.post(
        "/api/catalog/subjects",
        headers=admin_headers,
        json={"subject_code": code, "subject_name": name, "semester_number": semester},
    )
    assert response.status_code == 201, response.text


def _select(
    client: TestClient,
    headers: dict,
    code: str,
    academic_year: str,
    semester: int,
):
    return client.post(
        "/api/faculty/me/selections",
        headers=headers,
        json={
            "subject_code": code,
            "academic_year": academic_year,
            "semester_number": semester,
        },
    )


def _student_view(
    client: TestClient, headers: dict, academic_year: str, semester: int
) -> dict:
    response = client.get(
        "/api/students/me/dashboard",
        headers=headers,
        params={"academic_year": academic_year, "semester_number": semester},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_faculty_can_select_multiple_subjects_and_years(
    client: TestClient, data: dict, admin_headers: dict, faculty_a_headers: dict, student_headers: dict
) -> None:
    _create_subject(client, admin_headers, "CS601", "Machine Learning", 6)

    first = _select(client, faculty_a_headers, "CS601", "2026-27", 6)
    assert first.status_code == 200, first.text
    assert first.json()["created"] is True

    second_year = _select(client, faculty_a_headers, "CS601", "2027-28", 6)
    assert second_year.status_code == 200, second_year.text
    assert second_year.json()["created"] is True

    # Saving the same selection again is idempotent and never duplicates it.
    duplicate = _select(client, faculty_a_headers, "CS501", "2026-27", 5)
    assert duplicate.status_code == 200, duplicate.text
    assert duplicate.json()["created"] is False

    selections = client.get("/api/faculty/me/selections", headers=faculty_a_headers).json()
    keys = {(item["subject_code"], item["academic_year"], item["semester_number"]) for item in selections}
    assert keys == {
        ("CS501", "2026-27", 5),
        ("CS503", "2026-27", 5),
        ("CS601", "2026-27", 6),
        ("CS601", "2027-28", 6),
    }

    view_2026 = _student_view(client, student_headers, "2026-27", 6)
    assert [(item["subject_code"], item["faculty_name"]) for item in view_2026["offerings"]] == [
        ("CS601", "Faculty Alpha")
    ]

    view_2027 = _student_view(client, student_headers, "2027-28", 6)
    assert [(item["subject_code"], item["faculty_name"]) for item in view_2027["offerings"]] == [
        ("CS601", "Faculty Alpha")
    ]

    view_sem5 = _student_view(client, student_headers, "2026-27", 5)
    assert "CS601" not in {item["subject_code"] for item in view_sem5["offerings"]}


def test_selection_validation_and_duplicate_prevention(
    client: TestClient, data: dict, faculty_a_headers: dict, db: psycopg.Connection
) -> None:
    wrong_semester = _select(client, faculty_a_headers, "CS501", "2026-27", 6)
    assert wrong_semester.status_code == 400

    missing_subject = _select(client, faculty_a_headers, "CS999", "2026-27", 5)
    assert missing_subject.status_code == 404

    missing_year = _select(client, faculty_a_headers, "CS501", "2030-31", 5)
    assert missing_year.status_code == 400

    with db.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*)::int AS count FROM faculty_subject_selections WHERE faculty_id = %s",
            (data["faculty"]["a"],),
        )
        assert cur.fetchone()["count"] == 2


def test_faculty_can_update_and_remove_own_selection(
    client: TestClient, data: dict, admin_headers: dict, faculty_a_headers: dict
) -> None:
    _create_subject(client, admin_headers, "CS601", "Machine Learning", 6)
    created = _select(client, faculty_a_headers, "CS601", "2026-27", 6)
    assert created.status_code == 200, created.text
    selection_id = created.json()["selection"]["selection_id"]
    old_offering_id = created.json()["selection"]["offering_id"]
    assert old_offering_id is not None

    updated = client.put(
        f"/api/faculty/me/selections/{selection_id}",
        headers=faculty_a_headers,
        json={
            "subject_code": "CS601",
            "academic_year": "2027-28",
            "semester_number": 6,
        },
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["selection"]["academic_year"] == "2027-28"
    assert updated.json()["selection"]["offering_id"] != old_offering_id

    conflict = client.put(
        f"/api/faculty/me/selections/{selection_id}",
        headers=faculty_a_headers,
        json={
            "subject_code": "CS501",
            "academic_year": "2026-27",
            "semester_number": 5,
        },
    )
    assert conflict.status_code == 409

    removed = client.delete(
        f"/api/faculty/me/selections/{selection_id}", headers=faculty_a_headers
    )
    assert removed.status_code == 200, removed.text

    active = client.get("/api/faculty/me/selections", headers=faculty_a_headers).json()
    assert selection_id not in {item["selection_id"] for item in active}

    # Re-selecting reactivates the same row instead of creating a duplicate.
    reselected = _select(client, faculty_a_headers, "CS601", "2027-28", 6)
    assert reselected.status_code == 200, reselected.text
    assert reselected.json()["created"] is True
    assert reselected.json()["selection"]["selection_id"] == selection_id


def test_faculty_isolated_from_another_faculty_selection(
    client: TestClient, data: dict, faculty_a_headers: dict, faculty_b_headers: dict
) -> None:
    selection_id = data["selections"]["a"]

    update = client.put(
        f"/api/faculty/me/selections/{selection_id}",
        headers=faculty_b_headers,
        json={
            "subject_code": "CS502",
            "academic_year": "2026-27",
            "semester_number": 5,
        },
    )
    assert update.status_code == 404

    delete = client.delete(
        f"/api/faculty/me/selections/{selection_id}", headers=faculty_b_headers
    )
    assert delete.status_code == 404

    alpha = client.get("/api/faculty/me/selections", headers=faculty_a_headers).json()
    beta = client.get("/api/faculty/me/selections", headers=faculty_b_headers).json()
    assert {item["selection_id"] for item in alpha} == {
        data["selections"]["a"],
        data["selections"]["a2"],
    }
    assert {item["selection_id"] for item in beta} == {data["selections"]["b"]}


def test_unapproved_faculty_cannot_select(
    client: TestClient, data: dict
) -> None:
    pending_headers = bearer(data["faculty"]["pending"], "faculty")
    assert client.get("/api/faculty/me/selections", headers=pending_headers).status_code == 403
    assert _select(client, pending_headers, "CS501", "2026-27", 5).status_code == 403


def test_newly_approved_faculty_has_no_automatic_selections(
    client: TestClient, data: dict, admin_headers: dict, db: psycopg.Connection
) -> None:
    faculty_id = data["faculty"]["pending"]
    approved = client.patch(
        f"/api/admin/faculty/{faculty_id}/status",
        headers=admin_headers,
        json={"status": "approved"},
    )
    assert approved.status_code == 200, approved.text

    headers = bearer(faculty_id, "faculty")
    selections = client.get("/api/faculty/me/selections", headers=headers)
    assert selections.status_code == 200, selections.text
    assert selections.json() == []

    with db.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*)::int AS count FROM faculty_subject_selections WHERE faculty_id = %s",
            (faculty_id,),
        )
        assert cur.fetchone()["count"] == 0
        cur.execute(
            "SELECT COUNT(*)::int AS count FROM course_offerings WHERE faculty_id = %s",
            (faculty_id,),
        )
        assert cur.fetchone()["count"] == 0

    created = _select(client, headers, "CS501", "2027-28", 5)
    assert created.status_code == 200, created.text
    assert created.json()["selection"]["origin"] == "faculty"


def test_backfill_correction_deactivates_only_automatic_rows(
    client: TestClient, data: dict, db: psycopg.Connection
) -> None:
    with db.transaction():
        with db.cursor() as cur:
            # Simulate the earlier migration: an offering that existed before a
            # selection was inserted for it, sharing the original batch time.
            cur.execute(
                """
                INSERT INTO course_offerings
                    (academic_year, semester_number, subject_code, faculty_id, created_at)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP - INTERVAL '1 day')
                RETURNING offering_id
                """,
                ("2026-27", 5, "CS501", data["faculty"]["b"]),
            )
            automatic_offering = cur.fetchone()["offering_id"]
            cur.execute(
                """
                INSERT INTO faculty_subject_selections
                    (faculty_id, subject_code, academic_year, semester_number, is_active, created_at)
                VALUES (%s, %s, %s, %s, TRUE,
                        (SELECT MIN(created_at) FROM faculty_subject_selections))
                RETURNING selection_id
                """,
                (data["faculty"]["b"], "CS501", "2026-27", 5),
            )
            automatic_selection = cur.fetchone()["selection_id"]

            cur.execute(_CORRECTION_SQL)

            cur.execute(
                "SELECT is_active, origin FROM faculty_subject_selections WHERE selection_id = %s",
                (automatic_selection,),
            )
            corrected = cur.fetchone()
            assert corrected["is_active"] is False
            assert corrected["origin"] == "backfill"

            # Genuine seeded selections were created together with their
            # offerings, so they are left active and untouched.
            cur.execute(
                "SELECT is_active, origin FROM faculty_subject_selections WHERE selection_id = %s",
                (data["selections"]["a"],),
            )
            genuine = cur.fetchone()
            assert genuine["is_active"] is True
            assert genuine["origin"] == "faculty"

            # Historical offerings and feedback are never deleted.
            cur.execute(
                "SELECT COUNT(*)::int AS count FROM course_offerings WHERE offering_id = %s",
                (automatic_offering,),
            )
            assert cur.fetchone()["count"] == 1


def test_subject_request_requires_admin_approval(
    client: TestClient,
    data: dict,
    admin_headers: dict,
    faculty_a_headers: dict,
    faculty_b_headers: dict,
    student_headers: dict,
) -> None:
    requested = client.post(
        "/api/faculty/me/subject-requests",
        headers=faculty_a_headers,
        json={"subject_code": "cs701", "subject_name": "Cloud Computing", "semester_number": 7},
    )
    assert requested.status_code == 201, requested.text
    assert requested.json()["subject_code"] == "CS701"
    assert requested.json()["status"] == "pending"

    duplicate = client.post(
        "/api/faculty/me/subject-requests",
        headers=faculty_b_headers,
        json={"subject_code": "CS701", "subject_name": "Cloud Computing", "semester_number": 7},
    )
    assert duplicate.status_code == 409

    existing = client.post(
        "/api/faculty/me/subject-requests",
        headers=faculty_a_headers,
        json={"subject_code": "CS501", "subject_name": "Data Structures", "semester_number": 5},
    )
    assert existing.status_code == 409

    # The subject is not silently created and cannot be selected yet.
    catalog = client.get("/api/catalog/subjects", headers=admin_headers).json()
    assert "CS701" not in {item["subject_code"] for item in catalog}
    assert _select(client, faculty_a_headers, "CS701", "2026-27", 7).status_code == 404

    pending = client.get(
        "/api/admin/subject-requests", headers=admin_headers, params={"status": "pending"}
    ).json()
    assert [item["subject_code"] for item in pending["items"]] == ["CS701"]

    denied = client.patch(
        f"/api/admin/subject-requests/{requested.json()['request_id']}",
        headers=faculty_b_headers,
        json={"status": "approved"},
    )
    assert denied.status_code == 403

    approved = client.patch(
        f"/api/admin/subject-requests/{requested.json()['request_id']}",
        headers=admin_headers,
        json={"status": "approved", "admin_note": "Verified syllabus."},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"

    again = client.patch(
        f"/api/admin/subject-requests/{requested.json()['request_id']}",
        headers=admin_headers,
        json={"status": "approved"},
    )
    assert again.status_code == 409

    catalog = client.get("/api/catalog/subjects", headers=admin_headers).json()
    assert any(item["subject_code"] == "CS701" for item in catalog)

    # Approval adds the subject to the catalog; the faculty member still selects it.
    selected = _select(client, faculty_a_headers, "CS701", "2026-27", 7)
    assert selected.status_code == 200, selected.text
    view = _student_view(client, student_headers, "2026-27", 7)
    assert [(item["subject_code"], item["faculty_name"]) for item in view["offerings"]] == [
        ("CS701", "Faculty Alpha")
    ]

    rejected_request = client.post(
        "/api/faculty/me/subject-requests",
        headers=faculty_b_headers,
        json={"subject_code": "CS702", "subject_name": "Blockchain", "semester_number": 7},
    )
    assert rejected_request.status_code == 201, rejected_request.text
    rejected = client.patch(
        f"/api/admin/subject-requests/{rejected_request.json()['request_id']}",
        headers=admin_headers,
        json={"status": "rejected", "admin_note": "Not part of the approved curriculum."},
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["status"] == "rejected"
    catalog = client.get("/api/catalog/subjects", headers=admin_headers).json()
    assert "CS702" not in {item["subject_code"] for item in catalog}

    actions = {
        item["action"]
        for item in client.get("/api/admin/audit-logs", headers=admin_headers).json()["items"]
    }
    assert {"subject_request.create", "subject_request.review"} <= actions


def test_student_dashboard_hides_unassigned_and_unapproved_offerings(
    client: TestClient, data: dict, admin_headers: dict, student_headers: dict, db: psycopg.Connection
) -> None:
    _create_subject(client, admin_headers, "CS504", "Compiler Design", 5)
    _create_subject(client, admin_headers, "CS505", "Computer Networks", 5)

    with db.transaction():
        with db.cursor() as cur:
            # An offering without any faculty selection must stay invisible.
            cur.execute(
                """
                INSERT INTO course_offerings (academic_year, semester_number, subject_code, faculty_id)
                VALUES (%s, %s, %s, %s)
                """,
                ("2026-27", 5, "CS504", data["faculty"]["b"]),
            )
            # A selection owned by a pending faculty account is not eligible.
            cur.execute(
                """
                INSERT INTO course_offerings (academic_year, semester_number, subject_code, faculty_id)
                VALUES (%s, %s, %s, %s)
                """,
                ("2026-27", 5, "CS505", data["faculty"]["pending"]),
            )
            cur.execute(
                """
                INSERT INTO faculty_subject_selections
                    (faculty_id, subject_code, academic_year, semester_number, is_active)
                VALUES (%s, %s, %s, %s, TRUE)
                """,
                (data["faculty"]["pending"], "CS505", "2026-27", 5),
            )

    view = _student_view(client, student_headers, "2026-27", 5)
    codes = {item["subject_code"] for item in view["offerings"]}
    assert codes == {"CS501", "CS502", "CS503"}
    assert len({item["offering_id"] for item in view["offerings"]}) == len(view["offerings"])
    assert view["summary"]["pending"] == 3


def test_removing_selection_preserves_feedback_history(
    client: TestClient,
    data: dict,
    student_headers: dict,
    faculty_a_headers: dict,
    db: psycopg.Connection,
) -> None:
    created = submit_feedback(client, data, student_headers, offering_key="a", score=4)
    offering_id = data["offerings"]["a"]

    removed = client.delete(
        f"/api/faculty/me/selections/{data['selections']['a']}", headers=faculty_a_headers
    )
    assert removed.status_code == 200, removed.text
    assert "preserved" in removed.json()["message"].lower()

    view = _student_view(client, student_headers, "2026-27", 5)
    assert "CS501" not in {item["subject_code"] for item in view["offerings"]}

    # The feedback and its offering remain in the database for history.
    with db.cursor() as cur:
        cur.execute("SELECT COUNT(*)::int AS count FROM feedback WHERE feedback_id = %s", (created["feedback_id"],))
        assert cur.fetchone()["count"] == 1
        cur.execute("SELECT COUNT(*)::int AS count FROM course_offerings WHERE offering_id = %s", (offering_id,))
        assert cur.fetchone()["count"] == 1
        cur.execute(
            "SELECT is_active FROM faculty_subject_selections WHERE selection_id = %s",
            (data["selections"]["a"],),
        )
        assert cur.fetchone()["is_active"] is False

    submission = client.get(
        f"/api/students/me/feedback/{created['feedback_id']}/submission", headers=student_headers
    )
    assert submission.status_code == 200

    # Re-selecting restores the same offering, so the existing submission is kept.
    reselected = _select(client, faculty_a_headers, "CS501", "2026-27", 5)
    assert reselected.status_code == 200, reselected.text
    assert reselected.json()["selection"]["offering_id"] == offering_id
    assert reselected.json()["selection"]["response_count"] == 1

    view = _student_view(client, student_headers, "2026-27", 5)
    restored = next(item for item in view["offerings"] if item["subject_code"] == "CS501")
    assert restored["status"] == "submitted"
