"""Authentication, registration and approval rules."""

from __future__ import annotations

from fastapi.testclient import TestClient

from .conftest import TEST_PASSWORD


def test_first_admin_setup_runs_once(client: TestClient, db) -> None:
    status_before = client.get("/api/auth/setup-status")
    assert status_before.status_code == 200
    assert status_before.json() == {"completed": False}

    payload = {
        "name": "First Admin",
        "email": "first@test.local",
        "password": "StrongPass1",
        "confirm_password": "StrongPass1",
    }
    created = client.post("/api/auth/admin/setup", json=payload)
    assert created.status_code == 201, created.text
    assert created.json()["user"]["role"] == "admin"

    status_after = client.get("/api/auth/setup-status")
    assert status_after.json() == {"completed": True}

    again = client.post("/api/auth/admin/setup", json={**payload, "email": "second@test.local"})
    assert again.status_code == 403
    assert "sign in" in again.json()["detail"].lower()


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


def test_faculty_registration_does_not_create_duplicate_accounts(
    client: TestClient, data: dict, admin_headers: dict
) -> None:
    approved = client.post(
        "/api/auth/faculty/register",
        json={
            "name": "Duplicate Faculty",
            "email": "alpha@test.local",
            "department_id": data["department_id"],
            "password": "Faculty1Pass",
            "confirm_password": "Faculty1Pass",
        },
    )
    assert approved.status_code == 409
    assert "already registered" in approved.json()["detail"].lower()
    assert "sign in" in approved.json()["detail"].lower()

    pending = client.post(
        "/api/auth/faculty/register",
        json={
            "name": "Duplicate Pending",
            "email": "pending@test.local",
            "department_id": data["department_id"],
            "password": "Faculty1Pass",
            "confirm_password": "Faculty1Pass",
        },
    )
    assert pending.status_code == 409
    assert "awaiting administrator approval" in pending.json()["detail"].lower()

    faculty_list = client.get("/api/admin/faculty?page_size=100", headers=admin_headers).json()
    emails = [item["email"] for item in faculty_list["items"]]
    assert emails.count("alpha@test.local") == 1
    assert emails.count("pending@test.local") == 1


def test_login_errors_identify_the_actual_problem(client: TestClient, data: dict) -> None:
    missing_admin = client.post(
        "/api/auth/admin/login",
        json={"email": "missing-admin@test.local", "password": TEST_PASSWORD},
    )
    assert missing_admin.status_code == 401
    assert "no administrator account" in missing_admin.json()["detail"].lower()

    wrong_admin_password = client.post(
        "/api/auth/admin/login",
        json={"email": "admin@test.local", "password": "WrongPass1"},
    )
    assert wrong_admin_password.status_code == 401
    assert "incorrect password" in wrong_admin_password.json()["detail"].lower()

    valid_admin = client.post(
        "/api/auth/admin/login",
        json={"email": "  ADMIN@TEST.LOCAL  ", "password": TEST_PASSWORD},
    )
    assert valid_admin.status_code == 200, valid_admin.text
    assert valid_admin.json()["user"]["role"] == "admin"
    assert valid_admin.json()["user"]["email"] == "admin@test.local"

    missing_student = client.post(
        "/api/auth/student/login",
        json={"student_id": "4UB26CS999", "password": TEST_PASSWORD},
    )
    assert missing_student.status_code == 401
    assert "no student account" in missing_student.json()["detail"].lower()

    wrong_student_password = client.post(
        "/api/auth/student/login",
        json={"student_id": data["student_id"], "password": "WrongPass1"},
    )
    assert wrong_student_password.status_code == 401
    assert "incorrect password" in wrong_student_password.json()["detail"].lower()

    missing_faculty = client.post(
        "/api/auth/faculty/login",
        json={"email": "missing@test.local", "password": TEST_PASSWORD},
    )
    assert missing_faculty.status_code == 401
    assert "no faculty account" in missing_faculty.json()["detail"].lower()

    wrong_faculty_password = client.post(
        "/api/auth/faculty/login",
        json={"email": "alpha@test.local", "password": "WrongPass1"},
    )
    assert wrong_faculty_password.status_code == 401
    assert "incorrect password" in wrong_faculty_password.json()["detail"].lower()

    pending = client.post(
        "/api/auth/faculty/login",
        json={"email": "pending@test.local", "password": TEST_PASSWORD},
    )
    assert pending.status_code == 403
    assert "approval" in pending.json()["detail"].lower()


def test_inactive_admin_login_is_rejected_with_accurate_reason(
    client: TestClient, data: dict, db
) -> None:
    with db.transaction():
        with db.cursor() as cur:
            cur.execute(
                "UPDATE admins SET is_active = FALSE WHERE admin_id = %s",
                (data["admin_id"],),
            )

    response = client.post(
        "/api/auth/admin/login",
        json={"email": "admin@test.local", "password": TEST_PASSWORD},
    )
    assert response.status_code == 403
    assert "inactive" in response.json()["detail"].lower()


def test_only_admin_can_approve_or_reject_faculty(
    client: TestClient,
    data: dict,
    db,
    admin_headers: dict,
    faculty_a_headers: dict,
    student_headers: dict,
) -> None:
    pending_id = data["faculty"]["pending"]
    endpoint = f"/api/admin/faculty/{pending_id}/status"

    assert client.patch(endpoint, json={"status": "approved"}).status_code == 401
    assert (
        client.patch(endpoint, headers=student_headers, json={"status": "approved"}).status_code
        == 403
    )
    assert (
        client.patch(endpoint, headers=faculty_a_headers, json={"status": "approved"}).status_code
        == 403
    )

    approved = client.patch(endpoint, headers=admin_headers, json={"status": "approved"})
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"

    with db.cursor() as cur:
        cur.execute("SELECT status FROM faculty WHERE faculty_id = %s", (pending_id,))
        assert cur.fetchone()["status"] == "approved"

    created = client.post(
        "/api/auth/faculty/register",
        json={
            "name": "Reject Me",
            "email": "reject-me@test.local",
            "department_id": data["department_id"],
            "password": "Faculty1Pass",
            "confirm_password": "Faculty1Pass",
        },
    )
    assert created.status_code == 201, created.text
    rejected_id = next(
        item["faculty_id"]
        for item in client.get("/api/admin/faculty?page_size=100", headers=admin_headers).json()[
            "items"
        ]
        if item["email"] == "reject-me@test.local"
    )
    rejected = client.patch(
        f"/api/admin/faculty/{rejected_id}/status",
        headers=admin_headers,
        json={"status": "rejected"},
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["status"] == "rejected"

    with db.cursor() as cur:
        cur.execute("SELECT status FROM faculty WHERE faculty_id = %s", (rejected_id,))
        assert cur.fetchone()["status"] == "rejected"


def test_only_admin_can_create_administrator_accounts(
    client: TestClient,
    data: dict,
    admin_headers: dict,
    faculty_a_headers: dict,
    student_headers: dict,
) -> None:
    payload = {
        "name": "Another Administrator",
        "email": "another-admin@test.local",
        "password": "AnotherAdmin1Pass",
        "confirm_password": "AnotherAdmin1Pass",
    }

    assert client.post("/api/auth/admins", json=payload).status_code == 401
    assert (
        client.post("/api/auth/admins", headers=student_headers, json=payload).status_code == 403
    )
    assert (
        client.post("/api/auth/admins", headers=faculty_a_headers, json=payload).status_code == 403
    )

    created = client.post("/api/auth/admins", headers=admin_headers, json=payload)
    assert created.status_code == 201, created.text
    assert created.json()["user"]["role"] == "admin"

    login = client.post(
        "/api/auth/admin/login",
        json={"email": "ANOTHER-ADMIN@TEST.LOCAL", "password": "AnotherAdmin1Pass"},
    )
    assert login.status_code == 200, login.text
    assert login.json()["user"]["email"] == "another-admin@test.local"


def test_admin_can_archive_and_restore_student(
    client: TestClient,
    data: dict,
    admin_headers: dict,
    student_headers: dict,
) -> None:
    student_id = data["student_id"]
    endpoint = f"/api/admin/students/{student_id}/status"

    # The account works before archiving.
    assert client.get("/api/auth/me", headers=student_headers).status_code == 200

    archived = client.patch(endpoint, headers=admin_headers, json={"is_active": False})
    assert archived.status_code == 200, archived.text
    assert archived.json()["is_active"] is False

    # An already-issued token is rejected on the next request because every
    # protected request re-checks the database flag.
    assert client.get("/api/auth/me", headers=student_headers).status_code == 401
    assert client.get("/api/students/me/dashboard", headers=student_headers).status_code == 401

    blocked_login = client.post(
        "/api/auth/student/login",
        json={"student_id": student_id, "password": TEST_PASSWORD},
    )
    assert blocked_login.status_code == 403
    assert "inactive" in blocked_login.json()["detail"].lower()

    listed = client.get("/api/admin/students?page_size=100", headers=admin_headers).json()
    row = next(item for item in listed["items"] if item["student_id"] == student_id)
    assert row["is_active"] is False

    restored = client.patch(endpoint, headers=admin_headers, json={"is_active": True})
    assert restored.status_code == 200, restored.text
    assert restored.json()["is_active"] is True

    login_again = client.post(
        "/api/auth/student/login",
        json={"student_id": student_id, "password": TEST_PASSWORD},
    )
    assert login_again.status_code == 200, login_again.text


def test_only_admin_can_archive_students(
    client: TestClient,
    data: dict,
    admin_headers: dict,
    faculty_a_headers: dict,
    student_headers: dict,
) -> None:
    endpoint = f"/api/admin/students/{data['student_id']}/status"
    payload = {"is_active": False}

    assert client.patch(endpoint, json=payload).status_code == 401
    assert client.patch(endpoint, headers=student_headers, json=payload).status_code == 403
    assert client.patch(endpoint, headers=faculty_a_headers, json=payload).status_code == 403

    listed = client.get("/api/admin/students?page_size=100", headers=admin_headers).json()
    row = next(item for item in listed["items"] if item["student_id"] == data["student_id"])
    assert row["is_active"] is True

