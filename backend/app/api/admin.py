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
    StudentStatusUpdate,
    SubjectRequestReview,
)
from app.schemas.common import MessageResponse
from app.schemas.completion import EnrollmentBulkCreate, EnrollmentCreate
from app.services.audit import write_audit


router = APIRouter(prefix="/admin", tags=["Admin"])


def _validate_enrollment_scope(cur, subject_code: str, academic_year: str, semester_number: int) -> dict:
    """Validate the catalog scope before touching the roster.

    A roster row must always describe a real subject in its own semester and a
    real academic year. This keeps completion tracking aligned with the catalog
    and prevents typos from creating orphan scopes.
    """
    cur.execute(
        "SELECT subject_code, subject_name, semester_number FROM subjects WHERE subject_code = %s",
        (subject_code,),
    )
    subject = cur.fetchone()
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found in the catalog.")
    if subject["semester_number"] != semester_number:
        raise HTTPException(
            status_code=400,
            detail=(
                f"{subject_code} belongs to semester {subject['semester_number']}; "
                f"use semester {subject['semester_number']} for its roster."
            ),
        )
    cur.execute("SELECT 1 FROM academic_years WHERE academic_year = %s", (academic_year,))
    if cur.fetchone() is None:
        raise HTTPException(status_code=400, detail="Academic year is not available.")
    return subject


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
                   s.created_at, s.is_active, COUNT(fb.feedback_id)::int AS feedback_count
            FROM students s
            JOIN departments d ON d.id = s.department_id
            LEFT JOIN feedback fb ON fb.student_id = s.student_id
            WHERE {where}
            GROUP BY s.student_id, s.name, s.department_id, d.name, s.created_at, s.is_active
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


@router.patch("/students/{student_id}/status")
def update_student_status(
    student_id: str,
    payload: StudentStatusUpdate,
    request: Request,
    current_user: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    """Archive or restore a student account without deleting history.

    Archiving only flips ``is_active``: feedback, audit logs and foreign-key
    relationships are preserved, and every protected request re-checks the flag,
    so existing tokens stop working immediately.
    """
    normalized_id = normalize_usn(student_id)
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE students
                SET is_active = %s
                WHERE student_id = %s
                RETURNING student_id, name, is_active
                """,
                (payload.is_active, normalized_id),
            )
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Student not found.")
        write_audit(
            conn,
            current_user,
            "student.status_update",
            entity_type="student",
            entity_id=normalized_id,
            details={"is_active": payload.is_active},
            request=request,
        )
    return {
        **row,
        "message": (
            "Student account restored."
            if payload.is_active
            else "Student account archived. Existing sessions were invalidated."
        ),
    }


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
            SELECT s.student_id, s.name, s.department_id, d.name AS department_name,
                   s.created_at, s.is_active
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


@router.get("/enrollments")
def list_enrollments(
    subject_code: str = Query(min_length=2, max_length=20),
    academic_year: str = Query(pattern=r"^[0-9]{4}-[0-9]{2}$"),
    semester_number: int = Query(ge=1, le=8),
    _: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    """List the verified roster for one subject, year and semester."""
    code = subject_code.strip().upper()
    with conn.cursor() as cur:
        subject = _validate_enrollment_scope(cur, code, academic_year, semester_number)
        cur.execute(
            """
            SELECT se.enrollment_id, se.student_id, st.name, st.department_id,
                   d.name AS department_name, st.is_active, se.created_at
            FROM student_enrollments se
            JOIN students st ON st.student_id = se.student_id
            JOIN departments d ON d.id = st.department_id
            WHERE se.subject_code = %s
              AND se.academic_year = %s
              AND se.semester_number = %s
            ORDER BY se.student_id
            """,
            (code, academic_year, semester_number),
        )
        items = list(cur.fetchall())
    for item in items:
        item["created_at"] = item["created_at"].isoformat() if item["created_at"] else None
    return {
        "scope": {
            "subject_code": subject["subject_code"],
            "subject_name": subject["subject_name"],
            "academic_year": academic_year,
            "semester_number": semester_number,
        },
        "items": items,
        "total": len(items),
        "methodology": (
            "Only these students count as eligible for completion tracking. "
            "Registered students are never assumed to be enrolled."
        ),
    }


@router.post("/enrollments", status_code=status.HTTP_201_CREATED)
def add_enrollment(
    payload: EnrollmentCreate,
    request: Request,
    current_user: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    """Add one verified student to a class roster (idempotent)."""
    created = False
    with conn.transaction():
        with conn.cursor() as cur:
            _validate_enrollment_scope(
                cur, payload.subject_code, payload.academic_year, payload.semester_number
            )
            cur.execute(
                "SELECT student_id, name, is_active FROM students WHERE student_id = %s",
                (payload.student_id,),
            )
            student = cur.fetchone()
            if student is None:
                raise HTTPException(status_code=404, detail="Student not found.")
            if not student["is_active"]:
                raise HTTPException(
                    status_code=400,
                    detail="This student account is archived. Restore it before adding it to a roster.",
                )
            cur.execute(
                """
                INSERT INTO student_enrollments
                    (student_id, subject_code, academic_year, semester_number)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (student_id, subject_code, academic_year, semester_number)
                DO NOTHING
                RETURNING enrollment_id, created_at
                """,
                (
                    payload.student_id,
                    payload.subject_code,
                    payload.academic_year,
                    payload.semester_number,
                ),
            )
            row = cur.fetchone()
            created = row is not None
        if created:
            write_audit(
                conn,
                current_user,
                "student_enrollment.add",
                entity_type="student_enrollment",
                entity_id=row["enrollment_id"],
                details={
                    "student_id": payload.student_id,
                    "subject_code": payload.subject_code,
                    "academic_year": payload.academic_year,
                    "semester_number": payload.semester_number,
                },
                request=request,
            )
    return {
        "message": (
            "Student added to the verified roster."
            if created
            else "This student is already on the roster for this subject, year and semester."
        ),
        "created": created,
        "student_id": payload.student_id,
        "student_name": student["name"],
    }


@router.post("/enrollments/bulk", status_code=status.HTTP_201_CREATED)
def bulk_add_enrollments(
    payload: EnrollmentBulkCreate,
    request: Request,
    current_user: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    """Add up to 500 verified students at once.

    Unknown and archived accounts are reported back instead of being silently
    enrolled. Duplicate USNs in the request are collapsed before insertion.
    """
    requested = list(dict.fromkeys(payload.student_ids))
    added: list[str] = []
    with conn.transaction():
        with conn.cursor() as cur:
            _validate_enrollment_scope(
                cur, payload.subject_code, payload.academic_year, payload.semester_number
            )
            cur.execute(
                "SELECT student_id, is_active FROM students WHERE student_id = ANY(%s)",
                (requested,),
            )
            found = {row["student_id"]: row["is_active"] for row in cur.fetchall()}
            unknown = [student_id for student_id in requested if student_id not in found]
            inactive = [student_id for student_id in requested if found.get(student_id) is False]
            for student_id in requested:
                if found.get(student_id) is not True:
                    continue
                cur.execute(
                    """
                    INSERT INTO student_enrollments
                        (student_id, subject_code, academic_year, semester_number)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (student_id, subject_code, academic_year, semester_number)
                    DO NOTHING
                    RETURNING student_id
                    """,
                    (
                        student_id,
                        payload.subject_code,
                        payload.academic_year,
                        payload.semester_number,
                    ),
                )
                row = cur.fetchone()
                if row is not None:
                    added.append(row["student_id"])
        if added:
            write_audit(
                conn,
                current_user,
                "student_enrollment.bulk_add",
                entity_type="student_enrollment",
                entity_id=f"{payload.subject_code}:{payload.academic_year}:{payload.semester_number}",
                details={
                    "added": len(added),
                    "skipped_existing": len(requested) - len(added) - len(unknown) - len(inactive),
                    "unknown": len(unknown),
                    "inactive": len(inactive),
                },
                request=request,
            )
    return {
        "message": f"{len(added)} student(s) added to the verified roster.",
        "added": added,
        "added_count": len(added),
        "skipped_existing": len(requested) - len(added) - len(unknown) - len(inactive),
        "unknown": unknown,
        "inactive": inactive,
    }


@router.delete("/enrollments/{enrollment_id}", response_model=MessageResponse)
def remove_enrollment(
    enrollment_id: int,
    request: Request,
    current_user: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    """Remove one student from a roster without touching any feedback."""
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM student_enrollments
                WHERE enrollment_id = %s
                RETURNING enrollment_id, student_id, subject_code, academic_year, semester_number
                """,
                (enrollment_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Roster entry not found.")
        write_audit(
            conn,
            current_user,
            "student_enrollment.remove",
            entity_type="student_enrollment",
            entity_id=enrollment_id,
            details={
                "student_id": row["student_id"],
                "subject_code": row["subject_code"],
                "academic_year": row["academic_year"],
                "semester_number": row["semester_number"],
            },
            request=request,
        )
    return MessageResponse(message="Student removed from the verified roster. Feedback was not changed.")


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


@router.get("/subject-requests")
def list_subject_requests(
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=100),
    _: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    clauses = ["TRUE"]
    params: list = []
    if status_filter:
        if status_filter not in {"pending", "approved", "rejected"}:
            raise HTTPException(status_code=422, detail="Unknown subject request status.")
        clauses.append("sr.status = %s")
        params.append(status_filter)
    where = " AND ".join(clauses)
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*)::int AS total FROM subject_requests sr WHERE {where}", params)
        total = cur.fetchone()["total"]
        cur.execute(
            f"""
            SELECT sr.request_id, sr.faculty_id, f.name AS faculty_name, f.email AS faculty_email,
                   sr.subject_code, sr.subject_name, sr.semester_number, sr.status,
                   sr.admin_note, sr.reviewed_by, a.name AS reviewed_by_name,
                   sr.reviewed_at, sr.created_at,
                   EXISTS (SELECT 1 FROM subjects s WHERE s.subject_code = sr.subject_code) AS in_catalog
            FROM subject_requests sr
            JOIN faculty f ON f.faculty_id = sr.faculty_id
            LEFT JOIN admins a ON a.admin_id = sr.reviewed_by
            WHERE {where}
            ORDER BY CASE sr.status WHEN 'pending' THEN 0 ELSE 1 END,
                     sr.created_at DESC, sr.request_id DESC
            LIMIT %s OFFSET %s
            """,
            params + [page_size, (page - 1) * page_size],
        )
        items = list(cur.fetchall())
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.patch("/subject-requests/{request_id}")
def review_subject_request(
    request_id: int,
    payload: SubjectRequestReview,
    request: Request,
    current_user: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    """Approve or reject a faculty subject request.

    Approval only adds the subject to the official catalog. It never assigns the
    subject to the requesting faculty member; they select it themselves.
    """
    try:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT request_id, faculty_id, subject_code, subject_name, semester_number, status
                    FROM subject_requests WHERE request_id = %s FOR UPDATE
                    """,
                    (request_id,),
                )
                subject_request = cur.fetchone()
                if subject_request is None:
                    raise HTTPException(status_code=404, detail="Subject request not found.")
                if subject_request["status"] != "pending":
                    raise HTTPException(
                        status_code=409,
                        detail="This subject request has already been reviewed.",
                    )

                if payload.status == "approved":
                    cur.execute(
                        "SELECT subject_name, semester_number FROM subjects WHERE subject_code = %s",
                        (subject_request["subject_code"],),
                    )
                    existing = cur.fetchone()
                    if existing is not None:
                        same_name = existing["subject_name"].strip().lower() == subject_request["subject_name"].strip().lower()
                        same_semester = existing["semester_number"] == subject_request["semester_number"]
                        if not (same_name and same_semester):
                            raise HTTPException(
                                status_code=409,
                                detail="A different catalog subject already uses this subject code.",
                            )
                    else:
                        cur.execute(
                            """
                            INSERT INTO subjects (subject_code, subject_name, semester_number)
                            VALUES (%s, %s, %s)
                            """,
                            (
                                subject_request["subject_code"],
                                subject_request["subject_name"],
                                subject_request["semester_number"],
                            ),
                        )

                cur.execute(
                    """
                    UPDATE subject_requests
                    SET status = %s, admin_note = %s, reviewed_by = %s,
                        reviewed_at = CURRENT_TIMESTAMP
                    WHERE request_id = %s
                    RETURNING request_id, faculty_id, subject_code, subject_name,
                              semester_number, status, admin_note, reviewed_by,
                              reviewed_at, created_at
                    """,
                    (payload.status, payload.admin_note, int(current_user.id), request_id),
                )
                row = cur.fetchone()
            write_audit(
                conn,
                current_user,
                "subject_request.review",
                entity_type="subject_request",
                entity_id=request_id,
                details={
                    "status": payload.status,
                    "subject_code": row["subject_code"],
                },
                request=request,
            )
    except UniqueViolation as exc:
        raise HTTPException(
            status_code=409,
            detail="The catalog changed while this request was being approved. Review it again.",
        ) from exc
    return {
        **row,
        "message": (
            "Subject approved and added to the official catalog. The faculty member can now select it."
            if payload.status == "approved"
            else "Subject request rejected."
        ),
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
