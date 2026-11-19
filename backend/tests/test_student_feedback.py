"""Student feedback lifecycle, validation and anonymity rules."""

from __future__ import annotations

import psycopg
from fastapi.testclient import TestClient

from .conftest import ratings, submit_feedback


def test_dashboard_defaults_to_an_open_period(client: TestClient, data: dict, student_headers: dict) -> None:
    response = client.get("/api/students/me/dashboard", headers=student_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["selected"] == {"academic_year": "2026-27", "semester_number": 5}
    assert body["summary"]["pending"] == 3
    assert body["summary"]["closed"] == 0


def test_feedback_form_lists_active_questions(
    client: TestClient, data: dict, student_headers: dict
) -> None:
    offering_id = data["offerings"]["a"]
    response = client.get(f"/api/students/me/feedback/{offering_id}", headers=student_headers)
    assert response.status_code == 200
    body = response.json()
    assert [q["question_id"] for q in body["questions"]] == data["question_ids"]
    assert body["editable"] is True
    assert body["existing_feedback"] is None


def test_submit_then_duplicate_is_rejected(
    client: TestClient, data: dict, student_headers: dict
) -> None:
    first = submit_feedback(client, data, student_headers, offering_key="a", score=4)
    assert first["feedback_id"] > 0
    assert first["submitted_at"]

    duplicate = client.post(
        "/api/students/me/feedback",
        headers=student_headers,
        json={
            "offering_id": data["offerings"]["a"],
            "ratings": ratings(data, 4),
            "comment": "A second attempt that must not create another row.",
        },
    )
    assert duplicate.status_code == 409

    count = client.get("/api/students/me/dashboard", headers=student_headers).json()["summary"]
    assert count["submitted"] == 1


def test_edit_replaces_answers_atomically(
    client: TestClient, data: dict, student_headers: dict, db: psycopg.Connection
) -> None:
    created = submit_feedback(client, data, student_headers, offering_key="a", score=2)
    feedback_id = created["feedback_id"]

    response = client.put(
        f"/api/students/me/feedback/{feedback_id}",
        headers=student_headers,
        json={
            "ratings": ratings(data, 5),
            "comment": "After the revision sessions everything is much clearer now.",
        },
    )
    assert response.status_code == 200

    submission = client.get(
        f"/api/students/me/feedback/{feedback_id}/submission", headers=student_headers
    ).json()
    assert all(answer["rating"] == 5 for answer in submission["answers"])
    assert submission["updated_at"] is not None

    with db.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS count FROM feedback WHERE student_id = %s", (data["student_id"],))
        assert cur.fetchone()["count"] == 1
        cur.execute(
            "SELECT COUNT(*) AS count FROM feedback_answer WHERE feedback_id = %s", (feedback_id,)
        )
        assert cur.fetchone()["count"] == len(data["question_ids"])


def test_rating_validation(client: TestClient, data: dict, student_headers: dict) -> None:
    base = {
        "offering_id": data["offerings"]["a"],
        "ratings": ratings(data, 3),
        "comment": "A valid length comment for the validation checks.",
    }

    def post(**overrides):
        payload = {**base, **overrides}
        return client.post("/api/students/me/feedback", headers=student_headers, json=payload)

    bad_rating = [{"question_id": data["question_ids"][0], "rating": 6}]
    assert post(ratings=bad_rating).status_code == 422

    zero_rating = [{"question_id": data["question_ids"][0], "rating": 0}]
    assert post(ratings=zero_rating).status_code == 422

    missing = ratings(data, 3)[:-1]
    assert post(ratings=missing).status_code == 422

    extra = ratings(data, 3) + [{"question_id": 9999, "rating": 3}]
    assert post(ratings=extra).status_code == 422

    duplicated = ratings(data, 3) + [{"question_id": data["question_ids"][0], "rating": 3}]
    assert post(ratings=duplicated).status_code == 422

    assert post(comment="too short").status_code == 422
    assert post(comment="x" * 1001).status_code == 422


def test_closed_period_blocks_submission_and_editing(
    client: TestClient, data: dict, student_headers: dict, db: psycopg.Connection
) -> None:
    with db.transaction():
        with db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO course_offerings (academic_year, semester_number, subject_code, faculty_id)
                VALUES (%s, %s, %s, %s) RETURNING offering_id
                """,
                ("2027-28", 5, "CS501", data["faculty"]["a"]),
            )
            closed_offering = cur.fetchone()["offering_id"]

    response = client.post(
        "/api/students/me/feedback",
        headers=student_headers,
        json={
            "offering_id": closed_offering,
            "ratings": ratings(data, 4),
            "comment": "This period is closed, so the API must reject the submission.",
        },
    )
    assert response.status_code == 403

    created = submit_feedback(client, data, student_headers, offering_key="a", score=3)
    with db.transaction():
        with db.cursor() as cur:
            cur.execute(
                "UPDATE feedback_periods SET start_date = CURRENT_TIMESTAMP - INTERVAL '30 days', "
                "end_date = CURRENT_TIMESTAMP - INTERVAL '1 day' WHERE academic_year = %s",
                ("2026-27",),
            )
    read_only_form = client.get(
        f"/api/students/me/feedback/{data['offerings']['a']}", headers=student_headers
    )
    assert read_only_form.status_code == 200
    assert read_only_form.json()["editable"] is False
    assert read_only_form.json()["existing_feedback"]["feedback_id"] == created["feedback_id"]

    blocked = client.put(
        f"/api/students/me/feedback/{created['feedback_id']}",
        headers=student_headers,
        json={
            "ratings": ratings(data, 5),
            "comment": "Editing after the period closed must be rejected by the API.",
        },
    )
    assert blocked.status_code == 403


def test_students_cannot_edit_another_students_feedback(
    client: TestClient, data: dict, student_headers: dict
) -> None:
    created = submit_feedback(client, data, student_headers, offering_key="a", score=3)

    from .conftest import bearer

    other_headers = bearer(data["second_student_id"], "student")
    response = client.put(
        f"/api/students/me/feedback/{created['feedback_id']}",
        headers=other_headers,
        json={
            "ratings": ratings(data, 1),
            "comment": "Trying to tamper with somebody else's submission.",
        },
    )
    assert response.status_code == 404

    read = client.get(
        f"/api/students/me/feedback/{created['feedback_id']}/submission", headers=other_headers
    )
    assert read.status_code == 404


def test_two_students_can_rate_the_same_offering(
    client: TestClient, data: dict, student_headers: dict
) -> None:
    from .conftest import bearer

    submit_feedback(client, data, student_headers, offering_key="a", score=5)
    second = bearer(data["second_student_id"], "student")
    submit_feedback(client, data, second, offering_key="a", score=3)

    dashboard = client.get("/api/faculty/me/dashboard", headers=bearer(data["faculty"]["a"], "faculty"))
    assert dashboard.json()["overall"]["response_count"] == 2
