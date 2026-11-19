from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from psycopg import Connection
from psycopg.errors import UniqueViolation

from app.core.deps import Principal, student_required
from app.core.security import verify_password, hash_password, validate_password_strength
from app.db import get_db
from app.schemas.auth import ChangePassword
from app.schemas.common import MessageResponse
from app.schemas.feedback import FeedbackSubmit, FeedbackUpdate, RatingInput


router = APIRouter(prefix="/students/me", tags=["Student"])


def _comment(comment: str) -> str:
    cleaned = comment.strip()
    if len(cleaned) < 10 or len(cleaned) > 1000:
        raise HTTPException(status_code=422, detail="Comment must contain between 10 and 1000 characters.")
    return cleaned


def _offering_and_period(conn: Connection, offering_id: int, *, allow_closed: bool = False) -> dict:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT co.offering_id, co.academic_year, co.semester_number, co.subject_code,
                   co.faculty_id, s.subject_name, f.name AS faculty_name,
                   fp.start_date, fp.end_date,
                   (fp.academic_year IS NOT NULL AND CURRENT_TIMESTAMP BETWEEN fp.start_date AND fp.end_date) AS period_open
            FROM course_offerings co
            JOIN subjects s ON s.subject_code = co.subject_code
            JOIN faculty f ON f.faculty_id = co.faculty_id
            LEFT JOIN feedback_periods fp
              ON fp.academic_year = co.academic_year AND fp.semester_number = co.semester_number
            WHERE co.offering_id = %s
            """,
            (offering_id,),
        )
        offering = cur.fetchone()
    if offering is None:
        raise HTTPException(status_code=404, detail="Course offering not found.")
    if not offering["period_open"] and not allow_closed:
        raise HTTPException(status_code=403, detail="The feedback period is closed or not configured for this offering.")
    return offering


def _active_questions(conn: Connection) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT question_id, question_text FROM feedback_questions WHERE is_active = TRUE ORDER BY question_id"
        )
        questions = list(cur.fetchall())
    if not questions:
        raise HTTPException(status_code=400, detail="No active feedback questions are configured.")
    return questions


def _validate_ratings(conn: Connection, ratings: list[RatingInput]) -> None:
    question_ids = [item.question_id for item in ratings]
    if len(question_ids) != len(set(question_ids)):
        raise HTTPException(status_code=422, detail="Each question can be rated only once.")
    active = _active_questions(conn)
    active_ids = {question["question_id"] for question in active}
    submitted_ids = set(question_ids)
    missing = active_ids - submitted_ids
    extra = submitted_ids - active_ids
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Missing ratings for {len(missing)} active feedback question(s).",
        )
    if extra:
        raise HTTPException(status_code=422, detail="One or more question IDs are invalid or inactive.")


def _feedback_payload(conn: Connection, feedback_id: int, student_id: str) -> dict:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT fb.feedback_id, fb.offering_id, fb.comment, fb.submitted_at, fb.updated_at,
                   co.academic_year, co.semester_number, co.subject_code, s.subject_name,
                   f.name AS faculty_name,
                   COALESCE(
                     (fp.academic_year IS NOT NULL AND CURRENT_TIMESTAMP BETWEEN fp.start_date AND fp.end_date),
                     FALSE
                   ) AS editable
            FROM feedback fb
            JOIN course_offerings co ON co.offering_id = fb.offering_id
            JOIN subjects s ON s.subject_code = co.subject_code
            JOIN faculty f ON f.faculty_id = co.faculty_id
            LEFT JOIN feedback_periods fp
              ON fp.academic_year = co.academic_year AND fp.semester_number = co.semester_number
            WHERE fb.feedback_id = %s AND fb.student_id = %s
            """,
            (feedback_id, student_id),
        )
        feedback = cur.fetchone()
        if feedback is None:
            raise HTTPException(status_code=404, detail="Feedback submission not found.")
        cur.execute(
            """
            SELECT fa.question_id, fq.question_text, fa.rating
            FROM feedback_answer fa
            JOIN feedback_questions fq ON fq.question_id = fa.question_id
            WHERE fa.feedback_id = %s ORDER BY fq.question_id
            """,
            (feedback_id,),
        )
        feedback["answers"] = list(cur.fetchall())
    feedback["submitted_at"] = feedback["submitted_at"].isoformat()
    feedback["updated_at"] = feedback["updated_at"].isoformat() if feedback["updated_at"] else None
    feedback["start_date"] = None
    return feedback


@router.get("/profile")
def student_profile(
    current_user: Principal = Depends(student_required), conn: Connection = Depends(get_db)
):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT s.student_id, s.name, s.department_id, d.name AS department_name, s.created_at
            FROM students s JOIN departments d ON d.id = s.department_id
            WHERE s.student_id = %s
            """,
            (current_user.id,),
        )
        student = cur.fetchone()
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found.")
    student["created_at"] = student["created_at"].isoformat()
    return student


@router.get("/dashboard")
def student_dashboard(
    academic_year: str | None = Query(default=None),
    semester_number: int | None = Query(default=None, ge=1, le=8),
    current_user: Principal = Depends(student_required),
    conn: Connection = Depends(get_db),
):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT DISTINCT academic_year FROM course_offerings ORDER BY academic_year DESC"
        )
        years = [row["academic_year"] for row in cur.fetchall()]
        # Default to a year that currently has an open feedback period so that
        # students land on actionable offerings instead of a closed year.
        cur.execute(
            """
            SELECT DISTINCT academic_year FROM feedback_periods
            WHERE CURRENT_TIMESTAMP BETWEEN start_date AND end_date
            ORDER BY academic_year DESC
            """
        )
        open_years = [row["academic_year"] for row in cur.fetchall()]
        selected_year = academic_year or (open_years[0] if open_years else (years[0] if years else None))
        cur.execute(
            """
            SELECT DISTINCT co.semester_number
            FROM course_offerings co
            WHERE co.academic_year = %s
            ORDER BY co.semester_number
            """,
            (selected_year,),
        )
        semesters = [row["semester_number"] for row in cur.fetchall()]
        if semester_number:
            selected_semester = semester_number
        else:
            cur.execute(
                """
                SELECT semester_number FROM feedback_periods
                WHERE academic_year = %s
                  AND CURRENT_TIMESTAMP BETWEEN start_date AND end_date
                ORDER BY semester_number
                """,
                (selected_year,),
            )
            open_semesters = [row["semester_number"] for row in cur.fetchall()]
            selected_semester = open_semesters[0] if open_semesters else (semesters[0] if semesters else None)
        periods: list[dict] = []
        if selected_year:
            cur.execute(
                """
                SELECT semester_number, start_date, end_date,
                       (CURRENT_TIMESTAMP BETWEEN start_date AND end_date) AS is_open
                FROM feedback_periods WHERE academic_year = %s
                ORDER BY semester_number
                """,
                (selected_year,),
            )
            periods = list(cur.fetchall())
        offerings: list[dict] = []
        if selected_year and selected_semester:
            cur.execute(
                """
                SELECT co.offering_id, co.academic_year, co.semester_number, co.subject_code,
                       s.subject_name, co.faculty_id, f.name AS faculty_name,
                       fp.start_date, fp.end_date,
                       COALESCE(fp.academic_year IS NOT NULL AND CURRENT_TIMESTAMP BETWEEN fp.start_date AND fp.end_date, FALSE) AS period_open,
                       fb.feedback_id, fb.submitted_at
                FROM course_offerings co
                JOIN subjects s ON s.subject_code = co.subject_code
                JOIN faculty f ON f.faculty_id = co.faculty_id
                LEFT JOIN feedback_periods fp
                  ON fp.academic_year = co.academic_year AND fp.semester_number = co.semester_number
                LEFT JOIN feedback fb
                  ON fb.offering_id = co.offering_id AND fb.student_id = %s
                WHERE co.academic_year = %s AND co.semester_number = %s
                ORDER BY co.subject_code, f.name
                """,
                (current_user.id, selected_year, selected_semester),
            )
            offerings = list(cur.fetchall())
            for offering in offerings:
                offering["status"] = "submitted" if offering["feedback_id"] else ("pending" if offering["period_open"] else "closed")
                if offering["submitted_at"]:
                    offering["submitted_at"] = offering["submitted_at"].isoformat()
                if offering["start_date"]:
                    offering["start_date"] = offering["start_date"].isoformat()
                if offering["end_date"]:
                    offering["end_date"] = offering["end_date"].isoformat()
    submitted = sum(1 for item in offerings if item["status"] == "submitted")
    pending = sum(1 for item in offerings if item["status"] == "pending")
    closed = sum(1 for item in offerings if item["status"] == "closed")
    return {
        "student": {"student_id": current_user.id, "name": current_user.name},
        "filter_options": {"academic_years": years, "semesters": semesters, "periods": periods},
        "selected": {"academic_year": selected_year, "semester_number": selected_semester},
        "offerings": offerings,
        "summary": {"submitted": submitted, "pending": pending, "closed": closed, "total": len(offerings)},
    }


@router.get("/feedback/{offering_id}")
def get_feedback_form(
    offering_id: int,
    current_user: Principal = Depends(student_required),
    conn: Connection = Depends(get_db),
):
    offering = _offering_and_period(conn, offering_id, allow_closed=True)
    questions = _active_questions(conn)
    with conn.cursor() as cur:
        cur.execute(
            "SELECT feedback_id FROM feedback WHERE student_id = %s AND offering_id = %s",
            (current_user.id, offering_id),
        )
        existing = cur.fetchone()
    if not offering["period_open"] and existing is None:
        raise HTTPException(status_code=403, detail="The feedback period is closed or not configured for this offering.")
    result: dict[str, Any] = {
        "offering": offering,
        "questions": questions,
        "existing_feedback": None,
        "editable": offering["period_open"],
    }
    if existing:
        result["existing_feedback"] = _feedback_payload(conn, existing["feedback_id"], current_user.id)
    return result


@router.post("/feedback", status_code=status.HTTP_201_CREATED)
def submit_feedback(
    payload: FeedbackSubmit,
    current_user: Principal = Depends(student_required),
    conn: Connection = Depends(get_db),
):
    comment = _comment(payload.comment)
    offering = _offering_and_period(conn, payload.offering_id)
    _validate_ratings(conn, payload.ratings)
    try:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT feedback_id FROM feedback WHERE student_id = %s AND offering_id = %s",
                    (current_user.id, payload.offering_id),
                )
                if cur.fetchone() is not None:
                    raise HTTPException(
                        status_code=409,
                        detail="You already submitted feedback for this faculty member. Edit the existing submission instead.",
                    )
                cur.execute(
                    """
                    INSERT INTO feedback (student_id, offering_id, comment, submitted_at)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP) RETURNING feedback_id, submitted_at
                    """,
                    (current_user.id, payload.offering_id, comment),
                )
                feedback = cur.fetchone()
                for item in payload.ratings:
                    cur.execute(
                        "INSERT INTO feedback_answer (feedback_id, question_id, rating) VALUES (%s, %s, %s)",
                        (feedback["feedback_id"], item.question_id, item.rating),
                    )
    except UniqueViolation as exc:
        raise HTTPException(status_code=409, detail="Feedback has already been submitted for this offering.") from exc
    return {
        "message": "Feedback submitted successfully.",
        "feedback_id": feedback["feedback_id"],
        "submitted_at": feedback["submitted_at"].isoformat(),
        "faculty_name": offering["faculty_name"],
    }


@router.put("/feedback/{feedback_id}")
def update_feedback(
    feedback_id: int,
    payload: FeedbackUpdate,
    current_user: Principal = Depends(student_required),
    conn: Connection = Depends(get_db),
):
    comment = _comment(payload.comment)
    with conn.cursor() as cur:
        cur.execute(
            "SELECT offering_id FROM feedback WHERE feedback_id = %s AND student_id = %s",
            (feedback_id, current_user.id),
        )
        existing = cur.fetchone()
    if existing is None:
        raise HTTPException(status_code=404, detail="Feedback submission not found.")
    offering = _offering_and_period(conn, existing["offering_id"])
    _validate_ratings(conn, payload.ratings)
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                "SELECT feedback_id FROM feedback WHERE feedback_id = %s AND student_id = %s FOR UPDATE",
                (feedback_id, current_user.id),
            )
            if cur.fetchone() is None:
                raise HTTPException(status_code=404, detail="Feedback submission not found.")
            cur.execute(
                "UPDATE feedback SET comment = %s, updated_at = CURRENT_TIMESTAMP WHERE feedback_id = %s",
                (comment, feedback_id),
            )
            cur.execute("DELETE FROM feedback_answer WHERE feedback_id = %s", (feedback_id,))
            for item in payload.ratings:
                cur.execute(
                    "INSERT INTO feedback_answer (feedback_id, question_id, rating) VALUES (%s, %s, %s)",
                    (feedback_id, item.question_id, item.rating),
                )
    return {"message": "Feedback updated successfully.", "feedback_id": feedback_id, "faculty_name": offering["faculty_name"]}


@router.get("/feedback/{feedback_id}/submission")
def get_submission(
    feedback_id: int,
    current_user: Principal = Depends(student_required),
    conn: Connection = Depends(get_db),
):
    return _feedback_payload(conn, feedback_id, current_user.id)


@router.post("/change-password", response_model=MessageResponse)
def student_change_password(
    payload: ChangePassword,
    current_user: Principal = Depends(student_required),
    conn: Connection = Depends(get_db),
):
    validate_password_strength(payload.new_password)
    with conn.cursor() as cur:
        cur.execute("SELECT password_hash FROM students WHERE student_id = %s", (current_user.id,))
        row = cur.fetchone()
    if row is None or not verify_password(payload.current_password, row["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE students SET password_hash = %s WHERE student_id = %s",
                (hash_password(payload.new_password), current_user.id),
            )
    return MessageResponse(message="Password changed successfully.")
