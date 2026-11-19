"""Report exports and their access controls."""

from __future__ import annotations

from fastapi.testclient import TestClient

from .conftest import submit_feedback


def _seed_feedback(client: TestClient, data: dict, student_headers: dict) -> None:
    submit_feedback(
        client,
        data,
        student_headers,
        offering_key="a",
        score=4,
        comment="Clear explanations and helpful lab sessions throughout the semester.",
    )


def test_faculty_csv_report(
    client: TestClient, data: dict, student_headers: dict, faculty_a_headers: dict
) -> None:
    _seed_feedback(client, data, student_headers)
    response = client.get("/api/reports/faculty/me", headers=faculty_a_headers, params={"format": "csv"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    text = response.text
    assert "Faculty" in text or "faculty" in text
    assert "4.0" in text


def test_faculty_pdf_report(
    client: TestClient, data: dict, student_headers: dict, faculty_a_headers: dict
) -> None:
    _seed_feedback(client, data, student_headers)
    response = client.get("/api/reports/faculty/me", headers=faculty_a_headers, params={"format": "pdf"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_admin_reports(
    client: TestClient, data: dict, student_headers: dict, admin_headers: dict
) -> None:
    _seed_feedback(client, data, student_headers)
    csv_response = client.get("/api/reports/admin", headers=admin_headers, params={"format": "csv"})
    assert csv_response.status_code == 200
    assert csv_response.headers["content-type"].startswith("text/csv")

    pdf_response = client.get("/api/reports/admin", headers=admin_headers, params={"format": "pdf"})
    assert pdf_response.status_code == 200
    assert pdf_response.content.startswith(b"%PDF")


def test_students_cannot_download_reports(client: TestClient, student_headers: dict) -> None:
    assert client.get("/api/reports/faculty/me", headers=student_headers).status_code == 403
    assert client.get("/api/reports/admin", headers=student_headers).status_code == 403


def test_invalid_report_format_is_rejected(
    client: TestClient, faculty_a_headers: dict
) -> None:
    response = client.get(
        "/api/reports/faculty/me", headers=faculty_a_headers, params={"format": "xlsx"}
    )
    assert response.status_code == 422
