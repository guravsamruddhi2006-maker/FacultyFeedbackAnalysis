from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from psycopg import Connection
from psycopg.errors import UniqueViolation

from app.analytics.service import admin_dashboard, admin_faculty_comparison, faculty_analytics_for_admin
from app.core.deps import Principal, admin_required
from app.core.security import hash_password, normalize_email, normalize_usn
from app.db import get_db
from app.schemas.admin import (
    AdminStatusUpdate,
    FacultyAdminCreate,
    FacultyStatusUpdate,
    StudentAdminCreate,
    StudentAdminUpdate,
)
from app.schemas.common import MessageResponse
from app.services.audit import write_audit


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard")
def get_admin_dashboard(
    academic_year: str | None = None,
    semester_number: int | None = Query(default=None, ge=1, le=8),
    subject_code: str | None = None,
    faculty_id: int | None = None,
    _: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    return admin_dashboard(
        conn,
        academic_year=academic_year,
        semester_number=semester_number,
        subject_code=subject_code,
        faculty_id=faculty_id,
    )


@router.get("/faculty")
def list_faculty(
    status_filter: str | None = Query(default=None, alias="status"),
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    _: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    clauses = ["TRUE"]
    params: list = []
    if status_filter:
        clauses.append("f.status = %s")
        params.append(status_filter)
    if search:
        clauses.append("(f.name ILIKE %s OR f.email ILIKE %s)")
        params.extend([f"%{search.strip()}%"] * 2)
    where = " AND ".join(clauses)
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*)::int AS total FROM faculty f WHERE {where}", params)
        total = cur.fetchone()["total"]
        cur.execute(
            f"""
            SELECT f.faculty_id, f.name, f.email, f.department_id, d.name AS department_name,
                   f.status, f.created_at,
                   COUNT(DISTINCT co.offering_id)::int AS offering_count,
                   COUNT(DISTINCT fb.feedback_id)::int AS response_count
            FROM faculty f
            JOIN departments d ON d.id = f.department_id
            LEFT JOIN course_offerings co ON co.faculty_id = f.faculty_id
            LEFT JOIN feedback fb ON fb.offering_id = co.offering_id
            WHERE {where}
            GROUP BY f.faculty_id, f.name, f.email, f.department_id, d.name, f.status, f.created_at
            ORDER BY CASE f.status WHEN 'pending' THEN 0 ELSE 1 END, f.name
            LIMIT %s OFFSET %s
            """,
            params + [page_size, (page - 1) * page_size],
        )
        items = list(cur.fetchall())
    for item in items:
        item["created_at"] = item["created_at"].isoformat()
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/faculty", status_code=status.HTTP_201_CREATED)
def create_faculty_as_admin(
    payload: FacultyAdminCreate,
    request: Request,
    current_user: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    try:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM departments WHERE id = %s", (payload.department_id,))
                if cur.fetchone() is None:
                    raise HTTPException(status_code=404, detail="Department not found.")
                cur.execute(
                    """
                    INSERT INTO faculty (name, email, password_hash, department_id, status)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING faculty_id, name, email, department_id, status
                    """,
                    (
                        payload.name.strip(),
                        normalize_email(payload.email),
                        hash_password(payload.password),
                        payload.department_id,
                        payload.status,
                    ),
                )
                row = cur.fetchone()
            write_audit(conn, current_user, "faculty.create", entity_type="faculty", entity_id=row["faculty_id"], details={"email": row["email"]}, request=request)
            return row
    except UniqueViolation as exc:
        raise HTTPException(status_code=409, detail="A faculty account with this email already exists.") from exc


@router.patch("/faculty/{faculty_id}/status")
def update_faculty_status(
    faculty_id: int,
    payload: FacultyStatusUpdate,
    request: Request,
    current_user: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE faculty SET status = %s WHERE faculty_id = %s RETURNING faculty_id, name, email, status",
                (payload.status, faculty_id),
            )
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Faculty account not found.")
        write_audit(conn, current_user, "faculty.status_update", entity_type="faculty", entity_id=faculty_id, details={"status": payload.status}, request=request)
    return {**row, "message": f"Faculty account {payload.status}."}


@router.get("/students")
def list_students(
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    _: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    clauses = ["TRUE"]
    params: list = []
    if search:
        clauses.append("(s.student_id ILIKE %s OR s.name ILIKE %s)")
        params.extend([f"%{search.strip()}%"] * 2)
    where = " AND ".join(clauses)
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*)::int AS total FROM students s WHERE {where}", params)
        total = cur.fetchone()["total"]
        cur.execute(
            f"""
            SELECT s.student_id, s.name, s.department_id, d.name AS department_name,
                   s.created_at, COUNT(fb.feedback_id)::int AS feedback_count
            FROM students s
            JOIN departments d ON d.id = s.department_id
            LEFT JOIN feedback fb ON fb.student_id = s.student_id
            WHERE {where}
            GROUP BY s.student_id, s.name, s.department_id, d.name, s.created_at
            ORDER BY s.student_id
            LIMIT %s OFFSET %s
            """,
            params + [page_size, (page - 1) * page_size],
        )
        items = list(cur.fetchall())
    for item in items:
        item["created_at"] = item["created_at"].isoformat()
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/students", status_code=status.HTTP_201_CREATED)
def create_student_as_admin(
    payload: StudentAdminCreate,
    request: Request,
    current_user: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    try:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM departments WHERE id = %s", (payload.department_id,))
                if cur.fetchone() is None:
                    raise HTTPException(status_code=404, detail="Department not found.")
                cur.execute(
                    """
                    INSERT INTO students (student_id, name, department_id, password_hash)
                    VALUES (%s, %s, %s, %s)
                    RETURNING student_id, name, department_id
                    """,
                    (
                        normalize_usn(payload.student_id),
                        payload.name.strip(),
                        payload.department_id,
                        hash_password(payload.password),
                    ),
                )
                row = cur.fetchone()
            write_audit(conn, current_user, "student.create", entity_type="student", entity_id=row["student_id"], request=request)
            return row
    except UniqueViolation as exc:
        raise HTTPException(status_code=409, detail="A student with this USN already exists.") from exc


@router.patch("/students/{student_id}")
def update_student_as_admin(
    student_id: str,
    payload: StudentAdminUpdate,
    request: Request,
    current_user: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    normalized_id = normalize_usn(student_id)
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM departments WHERE id = %s", (payload.department_id,))
            if cur.fetchone() is None:
                raise HTTPException(status_code=404, detail="Department not found.")
            cur.execute(
                """
                UPDATE students
                SET name = %s, department_id = %s
                WHERE student_id = %s
                RETURNING student_id, name, department_id
                """,
                (payload.name.strip(), payload.department_id, normalized_id),
            )
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Student not found.")
        write_audit(
            conn,
            current_user,
            "student.update",
            entity_type="student",
            entity_id=normalized_id,
            details={"fields": ["name", "department_id"]},
            request=request,
        )
    return row


@router.get("/students/{student_id}")
def get_student_detail(
    student_id: str,
    request: Request,
    current_user: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT s.student_id, s.name, s.department_id, d.name AS department_name, s.created_at
            FROM students s JOIN departments d ON d.id = s.department_id
            WHERE s.student_id = %s
            """,
            (normalize_usn(student_id),),
        )
        student = cur.fetchone()
        if student is None:
            raise HTTPException(status_code=404, detail="Student not found.")
        cur.execute(
            """
            SELECT fb.feedback_id, fb.submitted_at, co.academic_year, co.semester_number,
                   co.subject_code, s.subject_name, f.name AS faculty_name
            FROM feedback fb
            JOIN course_offerings co ON co.offering_id = fb.offering_id
            JOIN subjects s ON s.subject_code = co.subject_code
            JOIN faculty f ON f.faculty_id = co.faculty_id
            WHERE fb.student_id = %s
            ORDER BY fb.submitted_at DESC
            """,
            (student["student_id"],),
        )
        submissions = list(cur.fetchall())
    for item in submissions:
        item["submitted_at"] = item["submitted_at"].isoformat()
    student["created_at"] = student["created_at"].isoformat()
    with conn.transaction():
        write_audit(
            conn,
            current_user,
            "student.identity_access",
            entity_type="student",
            entity_id=student["student_id"],
            details={"reason": "Admin viewed student-linked submission status"},
            request=request,
        )
    return {**student, "submissions": submissions, "audit_notice": "This access was recorded in the audit log."}


@router.get("/analytics/faculty/{faculty_id}")
def admin_view_faculty_analytics(
    faculty_id: int,
    academic_year: str | None = None,
    semester_number: int | None = Query(default=None, ge=1, le=8),
    subject_code: str | None = None,
    _: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    try:
        return faculty_analytics_for_admin(
            conn,
            faculty_id,
            academic_year=academic_year,
            semester_number=semester_number,
            subject_code=subject_code,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Faculty not found.") from exc


@router.get("/analytics/faculty-comparison")
def admin_compare_faculty(
    subject_code: str,
    academic_year: str | None = None,
    semester_number: int | None = Query(default=None, ge=1, le=8),
    _: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    return {
        "subject_code": subject_code,
        "faculty": admin_faculty_comparison(
            conn,
            subject_code=subject_code,
            academic_year=academic_year,
            semester_number=semester_number,
        ),
        "note": "Distinct faculty members are shown side by side; they are never merged as the same person.",
    }


@router.get("/admins")
def list_admins(
    _: Principal = Depends(admin_required), conn: Connection = Depends(get_db)
):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT admin_id, name, email, is_active, created_at FROM admins ORDER BY admin_id"
        )
        rows = list(cur.fetchall())
    for row in rows:
        row["created_at"] = row["created_at"].isoformat()
    return rows


@router.patch("/admins/{admin_id}/status")
def update_admin_status(
    admin_id: int,
    payload: AdminStatusUpdate,
    request: Request,
    current_user: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    if current_user.id == str(admin_id) and not payload.is_active:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own account.")
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE admins SET is_active = %s WHERE admin_id = %s RETURNING admin_id, name, email, is_active",
                (payload.is_active, admin_id),
            )
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Admin account not found.")
        write_audit(conn, current_user, "admin.status_update", entity_type="admin", entity_id=admin_id, details={"is_active": payload.is_active}, request=request)
    return row


@router.get("/audit-logs")
def list_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    action: str | None = None,
    _: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    clause = "WHERE action = %s" if action else ""
    params: list = [action] if action else []
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*)::int AS total FROM audit_logs {clause}", params)
        total = cur.fetchone()["total"]
        cur.execute(
            f"""
            SELECT log_id, actor_role, actor_id, action, entity_type, entity_id,
                   details, ip_address, created_at
            FROM audit_logs {clause}
            ORDER BY created_at DESC LIMIT %s OFFSET %s
            """,
            params + [page_size, (page - 1) * page_size],
        )
        items = list(cur.fetchall())
    for item in items:
        item["created_at"] = item["created_at"].isoformat()
    return {"items": items, "total": total, "page": page, "page_size": page_size}
