"""Authentication, registration and approval rules."""

from __future__ import annotations

from fastapi.testclient import TestClient

from .conftest import TEST_PASSWORD


def test_first_admin_setup_runs_once(client: TestClient, db) -> None:
    payload = {
        "name": "First Admin",
        "email": "first@test.local",
        "password": "StrongPass1",
        "confirm_password": "StrongPass1",
    }
    created = client.post("/api/auth/admin/setup", json=payload)
    assert created.status_code == 201, created.text
    assert created.json()["user"]["role"] == "admin"

    again = client.post("/api/auth/admin/setup", json={**payload, "email": "second@test.local"})
    assert again.status_code == 403


def test_student_registration_and_login(client: TestClient, data: dict) -> None:
    payload = {
        "student_id": "4UB26CS099",
        "name": "New Student",
        "department_id": data["department_id"],
        "password": "Student1Pass",
        "confirm_password": "Student1Pass",
    }
    created = client.post("/api/auth/student/register", json=payload)
    assert created.status_code == 201, created.text

    duplicate = client.post("/api/auth/student/register", json=payload)
    assert duplicate.status_code == 409

    login = client.post(
        "/api/auth/student/login",
        json={"student_id": "4UB26CS099", "password": "Student1Pass"},
    )
    assert login.status_code == 200, login.text
    assert login.json()["user"]["role"] == "student"

    wrong = client.post(
        "/api/auth/student/login",
        json={"student_id": "4UB26CS099", "password": "wrong-password"},
    )
    assert wrong.status_code == 401


def test_faculty_registration_requires_approval(
    client: TestClient, data: dict, admin_headers: dict
) -> None:
    payload = {
        "name": "Awaiting Approval",
        "email": "awaiting@test.local",
        "department_id": data["department_id"],
        "password": "Faculty1Pass",
        "confirm_password": "Faculty1Pass",
    }
    created = client.post("/api/auth/faculty/register", json=payload)
    assert created.status_code == 201, created.text

    blocked = client.post(
        "/api/auth/faculty/login",
        json={"email": "awaiting@test.local", "password": "Faculty1Pass"},
    )
    assert blocked.status_code == 403
    assert "approval" in blocked.json()["detail"].lower()

    faculty_list = client.get("/api/admin/faculty", headers=admin_headers).json()
    pending = next(item for item in faculty_list["items"] if item["email"] == "awaiting@test.local")
    assert pending["status"] == "pending"

    approved = client.patch(
        f"/api/admin/faculty/{pending['faculty_id']}/status",
        headers=admin_headers,
        json={"status": "approved"},
    )
    assert approved.status_code == 200

    login = client.post(
        "/api/auth/faculty/login",
        json={"email": "awaiting@test.local", "password": "Faculty1Pass"},
    )
    assert login.status_code == 200, login.text
    assert login.json()["user"]["role"] == "faculty"


def test_pending_faculty_token_is_rejected(client: TestClient, data: dict) -> None:
    from .conftest import bearer

    headers = bearer(data["faculty"]["pending"], "faculty")
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 403


def test_me_endpoint_returns_role_identity(
    client: TestClient, data: dict, admin_headers: dict, student_headers: dict
) -> None:
    admin = client.get("/api/auth/me", headers=admin_headers)
    assert admin.status_code == 200
    assert admin.json()["role"] == "admin"

    student = client.get("/api/auth/me", headers=student_headers)
    assert student.status_code == 200
    assert student.json()["id"] == data["student_id"]


def test_change_password(client: TestClient, data: dict) -> None:
    login = client.post(
        "/api/auth/student/login",
        json={"student_id": data["student_id"], "password": TEST_PASSWORD},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/api/students/me/change-password",
        headers=headers,
        json={
            "current_password": TEST_PASSWORD,
            "new_password": "BrandNew1Pass",
            "confirm_password": "BrandNew1Pass",
        },
    )
    assert response.status_code == 200

    old = client.post(
        "/api/auth/student/login",
        json={"student_id": data["student_id"], "password": TEST_PASSWORD},
    )
    assert old.status_code == 401
    new = client.post(
        "/api/auth/student/login",
        json={"student_id": data["student_id"], "password": "BrandNew1Pass"},
    )
    assert new.status_code == 200
