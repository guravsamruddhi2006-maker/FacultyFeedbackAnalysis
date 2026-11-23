from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from psycopg import Connection
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from app.core.deps import Principal, admin_required, authenticated, get_current_user
from app.db import get_db
from app.schemas.admin import (
    AcademicYearCreate,
    DepartmentCreate,
    DepartmentUpdate,
    FeedbackPeriodUpsert,
    FeedbackQuestionCreate,
    FeedbackQuestionUpdate,
    SubjectCreate,
    SubjectUpdate,
)
from app.schemas.common import MessageResponse
from app.services.audit import write_audit


router = APIRouter(prefix="/catalog", tags=["Catalog"])

# Fixed reference data that a fresh deployment needs before any course can be
# configured. Seeding is idempotent and never removes or overwrites user data.
BASE_DEPARTMENTS = (("Computer Science and Engineering", "CSE"),)
BASE_ACADEMIC_YEARS = ("2025-26", "2026-27", "2027-28", "2028-29")
BASE_QUESTIONS = (
    "Explains concepts clearly.",
    "Has good subject knowledge.",
    "Encourages student participation.",
    "Uses practical examples.",
    "Completes the syllabus.",
)


@router.get("/public/departments")
def public_departments(conn: Connection = Depends(get_db)):
    """Read-only department list used by the registration form."""
    with conn.cursor() as cur:
        cur.execute("SELECT id, name, code FROM departments ORDER BY name")
        return list(cur.fetchall())


@router.get("/departments")
def list_departments(
    _: Principal = Depends(authenticated), conn: Connection = Depends(get_db)
):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT d.id, d.name, d.code,
                   (SELECT COUNT(*) FROM faculty f WHERE f.department_id = d.id)::int AS faculty_count,
                   (SELECT COUNT(*) FROM students s WHERE s.department_id = d.id)::int AS student_count
            FROM departments d ORDER BY d.name
            """
        )
        return list(cur.fetchall())


@router.post("/departments", status_code=status.HTTP_201_CREATED)
def create_department(
    payload: DepartmentCreate,
    request: Request,
    current_user: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    try:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO departments (name, code) VALUES (%s, %s) RETURNING id, name, code",
                    (payload.name.strip(), payload.code),
                )
                row = cur.fetchone()
            write_audit(conn, current_user, "department.create", entity_type="department", entity_id=row["id"], request=request)
            return row
    except UniqueViolation as exc:
        raise HTTPException(status_code=409, detail="A department with this name or code already exists.") from exc


@router.put("/departments/{department_id}")
def update_department(
    department_id: int,
    payload: DepartmentUpdate,
    request: Request,
    current_user: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    try:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE departments SET name = %s, code = %s WHERE id = %s RETURNING id, name, code",
                    (payload.name.strip(), payload.code, department_id),
                )
                row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Department not found.")
            write_audit(conn, current_user, "department.update", entity_type="department", entity_id=department_id, request=request)
            return row
    except UniqueViolation as exc:
        raise HTTPException(status_code=409, detail="A department with this name or code already exists.") from exc


@router.delete("/departments/{department_id}", response_model=MessageResponse)
def delete_department(
    department_id: int,
    request: Request,
    current_user: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    try:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute("DELETE FROM departments WHERE id = %s", (department_id,))
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Department not found.")
            write_audit(conn, current_user, "department.delete", entity_type="department", entity_id=department_id, request=request)
    except ForeignKeyViolation as exc:
        raise HTTPException(status_code=409, detail="This department still has faculty or students.") from exc
    return MessageResponse(message="Department deleted.")


@router.get("/semesters")
def list_semesters(_: Principal = Depends(authenticated), conn: Connection = Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute("SELECT semester_number FROM semesters ORDER BY semester_number")
        return list(cur.fetchall())


@router.get("/academic-years")
def list_academic_years(_: Principal = Depends(authenticated), conn: Connection = Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute("SELECT academic_year FROM academic_years ORDER BY academic_year DESC")
        return list(cur.fetchall())


@router.post("/academic-years", status_code=status.HTTP_201_CREATED)
def create_academic_year(
    payload: AcademicYearCreate,
    request: Request,
    current_user: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    try:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO academic_years (academic_year) VALUES (%s) RETURNING academic_year",
                    (payload.academic_year,),
                )
                row = cur.fetchone()
            write_audit(conn, current_user, "academic_year.create", entity_type="academic_year", entity_id=payload.academic_year, request=request)
            return row
    except UniqueViolation as exc:
        raise HTTPException(status_code=409, detail="Academic year already exists.") from exc


@router.delete("/academic-years/{academic_year}", response_model=MessageResponse)
def delete_academic_year(
    academic_year: str,
    request: Request,
    current_user: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    try:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute("DELETE FROM academic_years WHERE academic_year = %s", (academic_year,))
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Academic year not found.")
            write_audit(conn, current_user, "academic_year.delete", entity_type="academic_year", entity_id=academic_year, request=request)
    except ForeignKeyViolation as exc:
        raise HTTPException(status_code=409, detail="This academic year still has course offerings.") from exc
    return MessageResponse(message="Academic year deleted.")


@router.get("/subjects")
def list_subjects(
    semester_number: int | None = Query(default=None, ge=1, le=8),
    search: str | None = None,
    _: Principal = Depends(authenticated),
    conn: Connection = Depends(get_db),
):
    clauses = ["TRUE"]
    params: list = []
    if semester_number:
        clauses.append("semester_number = %s")
        params.append(semester_number)
    if search:
        clauses.append("(subject_code ILIKE %s OR subject_name ILIKE %s)")
        params.extend([f"%{search.strip()}%", f"%{search.strip()}%"])
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT subject_code, subject_name, semester_number FROM subjects WHERE {' AND '.join(clauses)} ORDER BY semester_number, subject_code",
            params,
        )
        return list(cur.fetchall())


@router.post("/subjects", status_code=status.HTTP_201_CREATED)
def create_subject(
    payload: SubjectCreate,
    request: Request,
    current_user: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    try:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO subjects (subject_code, subject_name, semester_number)
                    VALUES (%s, %s, %s)
                    RETURNING subject_code, subject_name, semester_number
                    """,
                    (payload.subject_code, payload.subject_name.strip(), payload.semester_number),
                )
                row = cur.fetchone()
            write_audit(conn, current_user, "subject.create", entity_type="subject", entity_id=payload.subject_code, request=request)
            return row
    except UniqueViolation as exc:
        raise HTTPException(status_code=409, detail="Subject code already exists.") from exc
    except ForeignKeyViolation as exc:
        raise HTTPException(status_code=400, detail="Semester does not exist.") from exc


@router.put("/subjects/{subject_code}")
def update_subject(
    subject_code: str,
    payload: SubjectUpdate,
    request: Request,
    current_user: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    if subject_code != payload.subject_code:
        raise HTTPException(status_code=400, detail="Subject code cannot be changed here. Create a new subject instead.")
    try:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE subjects SET subject_name = %s, semester_number = %s
                    WHERE subject_code = %s RETURNING subject_code, subject_name, semester_number
                    """,
                    (payload.subject_name.strip(), payload.semester_number, subject_code),
                )
                row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Subject not found.")
            write_audit(conn, current_user, "subject.update", entity_type="subject", entity_id=subject_code, request=request)
            return row
    except ForeignKeyViolation as exc:
        raise HTTPException(status_code=400, detail="Semester does not exist.") from exc


@router.delete("/subjects/{subject_code}", response_model=MessageResponse)
def delete_subject(
    subject_code: str,
    request: Request,
    current_user: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    try:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute("DELETE FROM subjects WHERE subject_code = %s", (subject_code,))
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Subject not found.")
            write_audit(conn, current_user, "subject.delete", entity_type="subject", entity_id=subject_code, request=request)
    except ForeignKeyViolation as exc:
        raise HTTPException(status_code=409, detail="This subject is used by a course offering.") from exc
    return MessageResponse(message="Subject deleted.")


@router.get("/course-offerings")
def list_course_offerings(
    academic_year: str | None = None,
    semester_number: int | None = Query(default=None, ge=1, le=8),
    subject_code: str | None = None,
    faculty_id: int | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=100),
    _: Principal = Depends(authenticated),
    conn: Connection = Depends(get_db),
):
    """Read-only list of the offerings created by active faculty selections.

    Administrators manage the catalog and review subject requests. They do not
    create or delete faculty offerings; those follow the faculty member's own
    selection.
    """
    clauses = ["TRUE"]
    params: list = []
    if academic_year:
        clauses.append("co.academic_year = %s")
        params.append(academic_year)
    if semester_number:
        clauses.append("co.semester_number = %s")
        params.append(semester_number)
    if subject_code:
        clauses.append("co.subject_code = %s")
        params.append(subject_code)
    if faculty_id:
        clauses.append("co.faculty_id = %s")
        params.append(faculty_id)
    where = " AND ".join(clauses)
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT COUNT(*)::int AS total FROM course_offerings co WHERE {where}", params
        )
        total = cur.fetchone()["total"]
        cur.execute(
            f"""
            SELECT co.offering_id, co.academic_year, co.semester_number, co.subject_code,
                   s.subject_name, co.faculty_id, f.name AS faculty_name,
                   EXISTS (
                     SELECT 1 FROM feedback_periods fp
                     WHERE fp.academic_year = co.academic_year
                       AND fp.semester_number = co.semester_number
                       AND CURRENT_TIMESTAMP BETWEEN fp.start_date AND fp.end_date
                   ) AS period_open
            FROM course_offerings co
            JOIN subjects s ON s.subject_code = co.subject_code
            JOIN faculty f ON f.faculty_id = co.faculty_id
            WHERE {where}
            ORDER BY co.academic_year DESC, co.semester_number, co.subject_code, f.name
            LIMIT %s OFFSET %s
            """,
            params + [page_size, (page - 1) * page_size],
        )
        items = list(cur.fetchall())
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/feedback-questions")
def list_feedback_questions(
    include_inactive: bool = False,
    current_user: Principal = Depends(authenticated),
    conn: Connection = Depends(get_db),
):
    include = include_inactive and current_user.role == "admin"
    clause = "" if include else "WHERE is_active = TRUE"
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT question_id, question_text, is_active FROM feedback_questions {clause} ORDER BY question_id"
        )
        return list(cur.fetchall())


@router.post("/feedback-questions", status_code=status.HTTP_201_CREATED)
def create_feedback_question(
    payload: FeedbackQuestionCreate,
    request: Request,
    current_user: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO feedback_questions (question_text, is_active) VALUES (%s, %s) RETURNING question_id, question_text, is_active",
                (payload.question_text.strip(), payload.is_active),
            )
            row = cur.fetchone()
        write_audit(conn, current_user, "feedback_question.create", entity_type="feedback_question", entity_id=row["question_id"], request=request)
        return row


@router.put("/feedback-questions/{question_id}")
def update_feedback_question(
    question_id: int,
    payload: FeedbackQuestionUpdate,
    request: Request,
    current_user: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE feedback_questions SET question_text = %s, is_active = %s WHERE question_id = %s RETURNING question_id, question_text, is_active",
                (payload.question_text.strip(), payload.is_active, question_id),
            )
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Question not found.")
        write_audit(conn, current_user, "feedback_question.update", entity_type="feedback_question", entity_id=question_id, request=request)
        return row


@router.delete("/feedback-questions/{question_id}", response_model=MessageResponse)
def delete_feedback_question(
    question_id: int,
    request: Request,
    current_user: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    try:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute("DELETE FROM feedback_questions WHERE question_id = %s", (question_id,))
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Question not found.")
            write_audit(conn, current_user, "feedback_question.delete", entity_type="feedback_question", entity_id=question_id, request=request)
    except ForeignKeyViolation as exc:
        raise HTTPException(status_code=409, detail="This question already has answers. Deactivate it instead.") from exc
    return MessageResponse(message="Question deleted.")


@router.get("/feedback-periods")
def list_feedback_periods(
    academic_year: str | None = None,
    _: Principal = Depends(authenticated),
    conn: Connection = Depends(get_db),
):
    params: list = []
    clause = ""
    if academic_year:
        clause = "WHERE fp.academic_year = %s"
        params.append(academic_year)
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT fp.academic_year, fp.semester_number, fp.start_date, fp.end_date,
                   (CURRENT_TIMESTAMP BETWEEN fp.start_date AND fp.end_date) AS is_open
            FROM feedback_periods fp {clause}
            ORDER BY fp.academic_year DESC, fp.semester_number
            """,
            params,
        )
        return list(cur.fetchall())


@router.put("/feedback-periods")
def upsert_feedback_period(
    payload: FeedbackPeriodUpsert,
    request: Request,
    current_user: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO feedback_periods (academic_year, semester_number, start_date, end_date)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (academic_year, semester_number)
                DO UPDATE SET start_date = EXCLUDED.start_date, end_date = EXCLUDED.end_date
                RETURNING academic_year, semester_number, start_date, end_date
                """,
                (payload.academic_year, payload.semester_number, payload.start_date, payload.end_date),
            )
            row = cur.fetchone()
        write_audit(conn, current_user, "feedback_period.upsert", entity_type="feedback_period", entity_id=f"{payload.academic_year}:{payload.semester_number}", request=request)
        return row


@router.delete("/feedback-periods/{academic_year}/{semester_number}", response_model=MessageResponse)
def delete_feedback_period(
    academic_year: str,
    semester_number: int,
    request: Request,
    current_user: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM feedback_periods WHERE academic_year = %s AND semester_number = %s",
                (academic_year, semester_number),
            )
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Feedback period not found.")
        write_audit(conn, current_user, "feedback_period.delete", entity_type="feedback_period", entity_id=f"{academic_year}:{semester_number}", request=request)
    return MessageResponse(message="Feedback period deleted.")


@router.post("/bootstrap")
def bootstrap_base_catalog(
    request: Request,
    current_user: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    """Ensure the fixed reference catalog exists on a fresh deployment.

    Semesters are fixed academic reference data and cannot be created through
    the normal management forms, so this admin-only, idempotent operation
    inserts them along with the verified CSE department, base academic years
    and the default feedback questions. It never deletes or overwrites data.
    """
    created = {"semesters": 0, "departments": 0, "academic_years": 0, "questions": 0}
    with conn.transaction():
        with conn.cursor() as cur:
            for number in range(1, 9):
                cur.execute(
                    "INSERT INTO semesters (semester_number) VALUES (%s) ON CONFLICT DO NOTHING",
                    (number,),
                )
                created["semesters"] += cur.rowcount
            for name, code in BASE_DEPARTMENTS:
                cur.execute(
                    "INSERT INTO departments (name, code) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (name, code),
                )
                created["departments"] += cur.rowcount
            for year in BASE_ACADEMIC_YEARS:
                cur.execute(
                    "INSERT INTO academic_years (academic_year) VALUES (%s) ON CONFLICT DO NOTHING",
                    (year,),
                )
                created["academic_years"] += cur.rowcount
            cur.execute("SELECT COUNT(*)::int AS count FROM feedback_questions")
            if cur.fetchone()["count"] == 0:
                for question in BASE_QUESTIONS:
                    cur.execute(
                        "INSERT INTO feedback_questions (question_text) VALUES (%s)",
                        (question,),
                    )
                    created["questions"] += 1
        write_audit(
            conn,
            current_user,
            "catalog.bootstrap",
            entity_type="catalog",
            entity_id="base",
            details=created,
            request=request,
        )
    return {"message": "Base catalog is ready.", "created": created}
