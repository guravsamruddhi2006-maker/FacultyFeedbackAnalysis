"""Admin catalog management and audit trail."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient


def test_catalog_crud_flow(client: TestClient, data: dict, admin_headers: dict) -> None:
    department = client.post(
        "/api/catalog/departments",
        headers=admin_headers,
        json={"name": "Information Science", "code": "ise"},
    )
    assert department.status_code == 201, department.text
    assert department.json()["code"] == "ISE"

    year = client.post(
        "/api/catalog/academic-years", headers=admin_headers, json={"academic_year": "2028-29"}
    )
    assert year.status_code == 201, year.text

    subject = client.post(
        "/api/catalog/subjects",
        headers=admin_headers,
        json={"subject_code": "cs601", "subject_name": "Machine Learning", "semester_number": 6},
    )
    assert subject.status_code == 201, subject.text
    assert subject.json()["subject_code"] == "CS601"

    offering = client.post(
        "/api/catalog/course-offerings",
        headers=admin_headers,
        json={
            "academic_year": "2028-29",
            "semester_number": 6,
            "subject_code": "CS601",
            "faculty_id": data["faculty"]["a"],
        },
    )
    assert offering.status_code == 201, offering.text

    question = client.post(
        "/api/catalog/feedback-questions",
        headers=admin_headers,
        json={"question_text": "Provides timely feedback on assessments", "is_active": True},
    )
    assert question.status_code == 201, question.text

    now = datetime.now(timezone.utc)
    period = client.put(
        "/api/catalog/feedback-periods",
        headers=admin_headers,
        json={
            "academic_year": "2028-29",
            "semester_number": 6,
            "start_date": (now - timedelta(days=1)).isoformat(),
            "end_date": (now + timedelta(days=30)).isoformat(),
        },
    )
    assert period.status_code == 200, period.text

    offerings = client.get("/api/catalog/course-offerings", headers=admin_headers).json()["items"]
    assert any(item["subject_code"] == "CS601" for item in offerings)

    questions = client.get("/api/catalog/feedback-questions", headers=admin_headers).json()
    assert any(item["question_text"].startswith("Provides timely") for item in questions)

    periods = client.get("/api/catalog/feedback-periods", headers=admin_headers).json()
    assert any(item["academic_year"] == "2028-29" for item in periods)


def test_catalog_writes_require_admin(client: TestClient, data: dict, faculty_a_headers: dict) -> None:
    response = client.post(
        "/api/catalog/departments",
        headers=faculty_a_headers,
        json={"name": "Blocked Department", "code": "BLK"},
    )
    assert response.status_code == 403

    read = client.get("/api/catalog/departments", headers=faculty_a_headers)
    assert read.status_code == 200


def test_admin_can_create_faculty_and_student(
    client: TestClient, data: dict, admin_headers: dict
) -> None:
    faculty = client.post(
        "/api/admin/faculty",
        headers=admin_headers,
        json={
            "name": "Admin Created Faculty",
            "email": "created@test.local",
            "department_id": data["department_id"],
            "password": "Faculty1Pass",
            "status": "approved",
        },
    )
    assert faculty.status_code == 201, faculty.text

    student = client.post(
        "/api/admin/students",
        headers=admin_headers,
        json={
            "student_id": "4UB26CS077",
            "name": "Admin Created Student",
            "department_id": data["department_id"],
            "password": "Student1Pass",
        },
    )
    assert student.status_code == 201, student.text

    assert any(
        item["email"] == "created@test.local"
        for item in client.get("/api/admin/faculty", headers=admin_headers).json()["items"]
    )
    assert any(
        item["student_id"] == "4UB26CS077"
        for item in client.get("/api/admin/students", headers=admin_headers).json()["items"]
    )

    logs = client.get("/api/admin/audit-logs", headers=admin_headers).json()
    actions = {item["action"] for item in logs["items"]}
    assert "faculty.create" in actions
    assert "student.create" in actions


def test_student_updates_are_admin_only_and_audited(
    client: TestClient,
    data: dict,
    admin_headers: dict,
    faculty_a_headers: dict,
) -> None:
    payload = {"name": "Updated Test Student", "department_id": data["department_id"]}
    denied = client.patch(
        f"/api/admin/students/{data['student_id']}",
        headers=faculty_a_headers,
        json=payload,
    )
    assert denied.status_code == 403

    updated = client.patch(
        f"/api/admin/students/{data['student_id']}",
        headers=admin_headers,
        json=payload,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == payload["name"]
    assert updated.json()["student_id"] == data["student_id"]
    actions = {
        item["action"]
        for item in client.get("/api/admin/audit-logs", headers=admin_headers).json()["items"]
    }
    assert "student.update" in actions


def test_admin_can_deactivate_another_admin_but_not_self_lockout(
    client: TestClient, data: dict, admin_headers: dict
) -> None:
    created = client.post(
        "/api/auth/admins",
        headers=admin_headers,
        json={
            "name": "Second Admin",
            "email": "second-admin@test.local",
            "password": "Admin2Pass",
            "confirm_password": "Admin2Pass",
        },
    )
    assert created.status_code == 201, created.text
    second_id = created.json()["user"]["id"]

    deactivated = client.patch(
        f"/api/admin/admins/{second_id}/status", headers=admin_headers, json={"is_active": False}
    )
    assert deactivated.status_code == 200

    login = client.post(
        "/api/auth/admin/login",
        json={"email": "second-admin@test.local", "password": "Admin2Pass"},
    )
    assert login.status_code == 401


def test_admin_dashboard_counts(client: TestClient, data: dict, admin_headers: dict) -> None:
    response = client.get("/api/admin/dashboard", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["counts"]["total_students"] == 2
    assert body["counts"]["total_faculty"] == 3
    assert body["counts"]["pending_faculty"] == 1
