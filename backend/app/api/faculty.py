from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from psycopg import Connection
from psycopg.errors import UniqueViolation

from app.analytics.service import (
    faculty_dashboard as build_faculty_dashboard,
    get_filter_options,
    get_my_faculty_id,
    performance_comparison,
)
from app.analytics.text import analyze_comments, classify_topics, extract_keywords, predict_sentiment
from app.core.deps import Principal, faculty_required
from app.db import get_db
from app.schemas.common import MessageResponse
from app.schemas.faculty import (
    FacultySelectionCreate,
    FacultySelectionUpdate,
    SubjectRequestCreate,
)
from app.services.audit import write_audit
from app.services.completion_service import CompletionScopeNotFound, get_completion


router = APIRouter(prefix="/faculty/me", tags=["Faculty"])


SELECTION_SQL = """
    SELECT fss.selection_id, fss.faculty_id, fss.subject_code, s.subject_name,
           fss.academic_year, fss.semester_number, fss.is_active, fss.origin,
           fss.created_at, fss.updated_at,
           co.offering_id,
           COALESCE((
               SELECT COUNT(*) FROM feedback fb WHERE fb.offering_id = co.offering_id
           ), 0)::int AS response_count,
           COALESCE((
               SELECT CURRENT_TIMESTAMP BETWEEN fp.start_date AND fp.end_date
               FROM feedback_periods fp
               WHERE fp.academic_year = fss.academic_year
                 AND fp.semester_number = fss.semester_number
           ), FALSE) AS period_open
    FROM faculty_subject_selections fss
    JOIN subjects s ON s.subject_code = fss.subject_code
    LEFT JOIN course_offerings co
      ON co.faculty_id = fss.faculty_id
     AND co.subject_code = fss.subject_code
     AND co.academic_year = fss.academic_year
     AND co.semester_number = fss.semester_number
"""


def _selection(conn: Connection, selection_id: int, faculty_id: int) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            f"{SELECTION_SQL} WHERE fss.selection_id = %s AND fss.faculty_id = %s",
            (selection_id, faculty_id),
        )
        return cur.fetchone()


def _validate_target(
    cur, subject_code: str, academic_year: str, semester_number: int
) -> dict:
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
                f"select semester {subject['semester_number']} instead."
            ),
        )
    cur.execute("SELECT 1 FROM academic_years WHERE academic_year = %s", (academic_year,))
    if cur.fetchone() is None:
        raise HTTPException(status_code=400, detail="Academic year is not available.")
    return subject


def _offering_id(
    cur, faculty_id: int, subject_code: str, academic_year: str, semester_number: int
) -> int:
    cur.execute(
        """
        INSERT INTO course_offerings (academic_year, semester_number, subject_code, faculty_id)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (academic_year, semester_number, subject_code, faculty_id) DO NOTHING
        RETURNING offering_id
        """,
        (academic_year, semester_number, subject_code, faculty_id),
    )
    row = cur.fetchone()
    if row is not None:
        return row["offering_id"]
    cur.execute(
        """
        SELECT offering_id FROM course_offerings
        WHERE academic_year = %s AND semester_number = %s AND subject_code = %s AND faculty_id = %s
        """,
        (academic_year, semester_number, subject_code, faculty_id),
    )
    return cur.fetchone()["offering_id"]


def _find_offering(
    cur, faculty_id: int, subject_code: str, academic_year: str, semester_number: int
) -> int | None:
    cur.execute(
        """
        SELECT offering_id FROM course_offerings
        WHERE academic_year = %s AND semester_number = %s AND subject_code = %s AND faculty_id = %s
        """,
        (academic_year, semester_number, subject_code, faculty_id),
    )
    row = cur.fetchone()
    return row["offering_id"] if row else None


def _delete_offering_if_unused(cur, offering_id: int | None) -> bool:
    if offering_id is None:
        return False
    cur.execute("SELECT COUNT(*)::int AS count FROM feedback WHERE offering_id = %s", (offering_id,))
    if cur.fetchone()["count"] > 0:
        return False
    cur.execute("DELETE FROM course_offerings WHERE offering_id = %s", (offering_id,))
    return True



@router.get("/profile")
def faculty_profile(
    current_user: Principal = Depends(faculty_required), conn: Connection = Depends(get_db)
):
    faculty = get_my_faculty_id(conn, int(current_user.id))
    if faculty is None:
        raise HTTPException(status_code=404, detail="Faculty profile not found.")
    with conn.cursor() as cur:
        cur.execute("SELECT name FROM departments WHERE id = %s", (faculty["department_id"],))
        department = cur.fetchone()
        cur.execute(
            """
            SELECT COUNT(DISTINCT co.offering_id)::int AS offering_count,
                   COUNT(DISTINCT co.subject_code)::int AS subject_count
            FROM course_offerings co WHERE co.faculty_id = %s
            """,
            (current_user.id,),
        )
        summary = cur.fetchone()
        cur.execute(
            """
            SELECT co.academic_year, co.semester_number, co.subject_code, s.subject_name, co.offering_id
            FROM course_offerings co JOIN subjects s ON s.subject_code = co.subject_code
            WHERE co.faculty_id = %s
            ORDER BY co.academic_year DESC, co.semester_number, co.subject_code
            """,
            (current_user.id,),
        )
        offerings = list(cur.fetchall())
    return {
        **faculty,
        "department_name": department["name"] if department else None,
        "summary": summary,
        "offerings": offerings,
        "privacy_notice": "Students are anonymous. Identifiers are never exposed on this endpoint.",
    }


@router.get("/dashboard")
def faculty_dashboard(
    academic_year: str | None = None,
    semester_number: int | None = Query(default=None, ge=1, le=8),
    subject_code: str | None = None,
    current_user: Principal = Depends(faculty_required),
    conn: Connection = Depends(get_db),
):
    # The faculty_id is always the authenticated subject. No request input can change it.
    faculty_id = int(current_user.id)
    return build_faculty_dashboard(
        conn,
        faculty_id,
        academic_year=academic_year,
        semester_number=semester_number,
        subject_code=subject_code,
    )


@router.get("/completion")
def faculty_completion(
    subject_code: str = Query(min_length=2, max_length=20),
    academic_year: str = Query(pattern=r"^[0-9]{4}-[0-9]{2}$"),
    semester_number: int = Query(ge=1, le=8),
    current_user: Principal = Depends(faculty_required),
    conn: Connection = Depends(get_db),
):
    """Completion status for one of the authenticated faculty member's subjects.

    The faculty ID always comes from the JWT. The result is based on the verified
    roster and never includes feedback content, ratings or student-linked
    feedback identifiers.
    """
    try:
        return get_completion(
            conn,
            int(current_user.id),
            subject_code=subject_code.strip().upper(),
            academic_year=academic_year,
            semester_number=semester_number,
        )
    except CompletionScopeNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/comments")
def faculty_comments(
    academic_year: str | None = None,
    semester_number: int | None = Query(default=None, ge=1, le=8),
    subject_code: str | None = None,
    sentiment: str | None = Query(default=None, pattern="^(positive|neutral|negative)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: Principal = Depends(faculty_required),
    conn: Connection = Depends(get_db),
):
    clauses = ["co.faculty_id = %s", "trim(fb.comment) <> ''"]
    params: list = [current_user.id]
    if academic_year:
        clauses.append("co.academic_year = %s")
        params.append(academic_year)
    if semester_number:
        clauses.append("co.semester_number = %s")
        params.append(semester_number)
    if subject_code:
        clauses.append("co.subject_code = %s")
        params.append(subject_code)
    where = " AND ".join(clauses)
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT fb.feedback_id, fb.comment, fb.submitted_at,
                   co.academic_year, co.semester_number, co.subject_code, s.subject_name
            FROM feedback fb
            JOIN course_offerings co ON co.offering_id = fb.offering_id
            JOIN subjects s ON s.subject_code = co.subject_code
            WHERE {where}
            ORDER BY fb.submitted_at DESC
            """,
            params,
        )
        rows = list(cur.fetchall())
    enriched = []
    for row in rows:
        analysis = predict_sentiment(row["comment"])
        if sentiment and analysis["label"] != sentiment:
            continue
        row["submitted_at"] = row["submitted_at"].isoformat()
        row["sentiment"] = analysis
        enriched.append(row)
    total = len(enriched)
    start = (page - 1) * page_size
    return {
        "items": enriched[start:start + page_size],
        "total": total,
        "page": page,
        "page_size": page_size,
        "privacy_notice": "Anonymous comments only. Student identifiers are not stored in this response.",
    }


@router.get("/trends")
def faculty_trends(
    subject_code: str | None = None,
    current_user: Principal = Depends(faculty_required),
    conn: Connection = Depends(get_db),
):
    return performance_comparison(conn, int(current_user.id), subject_code=subject_code)


@router.get("/offerings")
def faculty_offerings(
    current_user: Principal = Depends(faculty_required), conn: Connection = Depends(get_db)
):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT co.offering_id, co.academic_year, co.semester_number, co.subject_code,
                   s.subject_name,
                   COUNT(DISTINCT fb.feedback_id)::int AS response_count,
                   EXISTS (
                     SELECT 1 FROM feedback_periods fp
                     WHERE fp.academic_year = co.academic_year
                       AND fp.semester_number = co.semester_number
                       AND CURRENT_TIMESTAMP BETWEEN fp.start_date AND fp.end_date
                   ) AS period_open
            FROM course_offerings co
            JOIN subjects s ON s.subject_code = co.subject_code
            LEFT JOIN feedback fb ON fb.offering_id = co.offering_id
            WHERE co.faculty_id = %s
            GROUP BY co.offering_id, co.academic_year, co.semester_number, co.subject_code, s.subject_name
            ORDER BY co.academic_year DESC, co.semester_number, co.subject_code
            """,
            (current_user.id,),
        )
        return list(cur.fetchall())


@router.get("/filter-options")
def faculty_filter_options(
    current_user: Principal = Depends(faculty_required), conn: Connection = Depends(get_db)
):
    return get_filter_options(conn, faculty_id=int(current_user.id))


@router.get("/sentiment")
def faculty_sentiment(
    academic_year: str | None = None,
    semester_number: int | None = Query(default=None, ge=1, le=8),
    subject_code: str | None = None,
    current_user: Principal = Depends(faculty_required),
    conn: Connection = Depends(get_db),
):
    clauses = ["co.faculty_id = %s", "trim(fb.comment) <> ''"]
    params: list = [current_user.id]
    if academic_year:
        clauses.append("co.academic_year = %s")
        params.append(academic_year)
    if semester_number:
        clauses.append("co.semester_number = %s")
        params.append(semester_number)
    if subject_code:
        clauses.append("co.subject_code = %s")
        params.append(subject_code)
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT fb.comment
            FROM feedback fb
            JOIN course_offerings co ON co.offering_id = fb.offering_id
            WHERE {' AND '.join(clauses)}
            """,
            params,
        )
        comments = [row["comment"] for row in cur.fetchall()]
    return {
        "summary": analyze_comments(comments),
        "topics": classify_topics(comments),
        "keywords": extract_keywords(comments),
    }


@router.get("/selections")
def list_my_selections(
    current_user: Principal = Depends(faculty_required), conn: Connection = Depends(get_db)
):
    """Return the authenticated faculty member's active selections.

    The faculty ID always comes from the JWT. No request parameter can widen the
    scope to another faculty member.
    """
    with conn.cursor() as cur:
        cur.execute(
            f"{SELECTION_SQL} WHERE fss.faculty_id = %s AND fss.is_active = TRUE "
            "ORDER BY fss.academic_year DESC, fss.semester_number, fss.subject_code",
            (int(current_user.id),),
        )
        return list(cur.fetchall())


@router.post("/selections")
def create_my_selection(
    payload: FacultySelectionCreate,
    request: Request,
    current_user: Principal = Depends(faculty_required),
    conn: Connection = Depends(get_db),
):
    faculty_id = int(current_user.id)
    created = False
    with conn.transaction():
        with conn.cursor() as cur:
            _validate_target(cur, payload.subject_code, payload.academic_year, payload.semester_number)
            cur.execute(
                """
                SELECT selection_id, is_active FROM faculty_subject_selections
                WHERE faculty_id = %s AND subject_code = %s AND academic_year = %s AND semester_number = %s
                FOR UPDATE
                """,
                (faculty_id, payload.subject_code, payload.academic_year, payload.semester_number),
            )
            existing = cur.fetchone()
            if existing is None:
                cur.execute(
                    """
                    INSERT INTO faculty_subject_selections
                        (faculty_id, subject_code, academic_year, semester_number, is_active, origin)
                    VALUES (%s, %s, %s, %s, TRUE, 'faculty')
                    RETURNING selection_id
                    """,
                    (faculty_id, payload.subject_code, payload.academic_year, payload.semester_number),
                )
                selection_id = cur.fetchone()["selection_id"]
                created = True
            else:
                selection_id = existing["selection_id"]
                if not existing["is_active"]:
                    cur.execute(
                        """
                        UPDATE faculty_subject_selections
                        SET is_active = TRUE, origin = 'faculty', updated_at = CURRENT_TIMESTAMP
                        WHERE selection_id = %s
                        """,
                        (selection_id,),
                    )
                    created = True
            _offering_id(
                cur,
                faculty_id,
                payload.subject_code,
                payload.academic_year,
                payload.semester_number,
            )
        write_audit(
            conn,
            current_user,
            "faculty_selection.create" if created else "faculty_selection.confirm",
            entity_type="faculty_selection",
            entity_id=selection_id,
            details={
                "subject_code": payload.subject_code,
                "academic_year": payload.academic_year,
                "semester_number": payload.semester_number,
            },
            request=request,
        )
        row = _selection(conn, selection_id, faculty_id)
    return {
        "message": "Subject selected." if created else "This subject is already selected for that year and semester.",
        "created": created,
        "selection": row,
    }


@router.put("/selections/{selection_id}")
def update_my_selection(
    selection_id: int,
    payload: FacultySelectionUpdate,
    request: Request,
    current_user: Principal = Depends(faculty_required),
    conn: Connection = Depends(get_db),
):
    faculty_id = int(current_user.id)
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT selection_id, subject_code, academic_year, semester_number, is_active
                FROM faculty_subject_selections
                WHERE selection_id = %s AND faculty_id = %s
                FOR UPDATE
                """,
                (selection_id, faculty_id),
            )
            selection = cur.fetchone()
            if selection is None or not selection["is_active"]:
                raise HTTPException(status_code=404, detail="Subject selection not found.")

            _validate_target(cur, payload.subject_code, payload.academic_year, payload.semester_number)
            key_changed = (
                selection["subject_code"],
                selection["academic_year"],
                selection["semester_number"],
            ) != (payload.subject_code, payload.academic_year, payload.semester_number)

            if key_changed:
                cur.execute(
                    """
                    SELECT selection_id FROM faculty_subject_selections
                    WHERE faculty_id = %s AND subject_code = %s AND academic_year = %s
                      AND semester_number = %s AND selection_id <> %s
                    FOR UPDATE
                    """,
                    (
                        faculty_id,
                        payload.subject_code,
                        payload.academic_year,
                        payload.semester_number,
                        selection_id,
                    ),
                )
                if cur.fetchone() is not None:
                    raise HTTPException(
                        status_code=409,
                        detail="You already have a selection for this subject, year and semester.",
                    )

                old_offering = _find_offering(
                    cur,
                    faculty_id,
                    selection["subject_code"],
                    selection["academic_year"],
                    selection["semester_number"],
                )
                if old_offering is not None:
                    cur.execute(
                        "SELECT COUNT(*)::int AS count FROM feedback WHERE offering_id = %s",
                        (old_offering,),
                    )
                    if cur.fetchone()["count"] > 0:
                        raise HTTPException(
                            status_code=409,
                            detail="This selection already has feedback. Remove it without changing it to preserve history.",
                        )
                    cur.execute("DELETE FROM course_offerings WHERE offering_id = %s", (old_offering,))

            cur.execute(
                """
                UPDATE faculty_subject_selections
                SET subject_code = %s, academic_year = %s, semester_number = %s,
                    is_active = TRUE, origin = 'faculty', updated_at = CURRENT_TIMESTAMP
                WHERE selection_id = %s
                """,
                (
                    payload.subject_code,
                    payload.academic_year,
                    payload.semester_number,
                    selection_id,
                ),
            )
            _offering_id(
                cur,
                faculty_id,
                payload.subject_code,
                payload.academic_year,
                payload.semester_number,
            )
        write_audit(
            conn,
            current_user,
            "faculty_selection.update",
            entity_type="faculty_selection",
            entity_id=selection_id,
            details={
                "subject_code": payload.subject_code,
                "academic_year": payload.academic_year,
                "semester_number": payload.semester_number,
            },
            request=request,
        )
        row = _selection(conn, selection_id, faculty_id)
    return {"message": "Subject selection updated.", "selection": row}


@router.delete("/selections/{selection_id}", response_model=MessageResponse)
def remove_my_selection(
    selection_id: int,
    request: Request,
    current_user: Principal = Depends(faculty_required),
    conn: Connection = Depends(get_db),
):
    faculty_id = int(current_user.id)
    feedback_preserved = False
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT selection_id, subject_code, academic_year, semester_number, is_active
                FROM faculty_subject_selections
                WHERE selection_id = %s AND faculty_id = %s
                FOR UPDATE
                """,
                (selection_id, faculty_id),
            )
            selection = cur.fetchone()
            if selection is None or not selection["is_active"]:
                raise HTTPException(status_code=404, detail="Subject selection not found.")

            offering_id = _find_offering(
                cur,
                faculty_id,
                selection["subject_code"],
                selection["academic_year"],
                selection["semester_number"],
            )
            deleted = _delete_offering_if_unused(cur, offering_id)
            feedback_preserved = offering_id is not None and not deleted

            cur.execute(
                """
                UPDATE faculty_subject_selections
                SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE selection_id = %s
                """,
                (selection_id,),
            )
        write_audit(
            conn,
            current_user,
            "faculty_selection.remove",
            entity_type="faculty_selection",
            entity_id=selection_id,
            details={
                "subject_code": selection["subject_code"],
                "academic_year": selection["academic_year"],
                "semester_number": selection["semester_number"],
                "feedback_preserved": feedback_preserved,
            },
            request=request,
        )
    message = (
        "Selection removed. Existing feedback was preserved."
        if feedback_preserved
        else "Selection removed."
    )
    return MessageResponse(message=message)


@router.get("/subject-requests")
def list_my_subject_requests(
    current_user: Principal = Depends(faculty_required), conn: Connection = Depends(get_db)
):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT sr.request_id, sr.faculty_id, sr.subject_code, sr.subject_name,
                   sr.semester_number, sr.status, sr.admin_note, sr.reviewed_by,
                   sr.reviewed_at, sr.created_at,
                   EXISTS (SELECT 1 FROM subjects s WHERE s.subject_code = sr.subject_code) AS in_catalog
            FROM subject_requests sr
            WHERE sr.faculty_id = %s
            ORDER BY sr.created_at DESC, sr.request_id DESC
            """,
            (int(current_user.id),),
        )
        return list(cur.fetchall())


@router.post("/subject-requests", status_code=status.HTTP_201_CREATED)
def create_my_subject_request(
    payload: SubjectRequestCreate,
    request: Request,
    current_user: Principal = Depends(faculty_required),
    conn: Connection = Depends(get_db),
):
    faculty_id = int(current_user.id)
    try:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM subjects WHERE subject_code = %s", (payload.subject_code,)
                )
                if cur.fetchone() is not None:
                    raise HTTPException(
                        status_code=409,
                        detail="This subject code is already in the official catalog.",
                    )
                cur.execute(
                    "SELECT 1 FROM subject_requests WHERE subject_code = %s AND status = 'pending'",
                    (payload.subject_code,),
                )
                if cur.fetchone() is not None:
                    raise HTTPException(
                        status_code=409,
                        detail="A pending request already exists for this subject code.",
                    )
                cur.execute("SELECT 1 FROM semesters WHERE semester_number = %s", (payload.semester_number,))
                if cur.fetchone() is None:
                    raise HTTPException(status_code=400, detail="Semester is not available.")
                cur.execute(
                    """
                    INSERT INTO subject_requests
                        (faculty_id, subject_code, subject_name, semester_number)
                    VALUES (%s, %s, %s, %s)
                    RETURNING request_id, faculty_id, subject_code, subject_name,
                              semester_number, status, admin_note, reviewed_by,
                              reviewed_at, created_at
                    """,
                    (
                        faculty_id,
                        payload.subject_code,
                        payload.subject_name,
                        payload.semester_number,
                    ),
                )
                row = cur.fetchone()
            write_audit(
                conn,
                current_user,
                "subject_request.create",
                entity_type="subject_request",
                entity_id=row["request_id"],
                details={
                    "subject_code": payload.subject_code,
                    "semester_number": payload.semester_number,
                },
                request=request,
            )
    except UniqueViolation as exc:
        raise HTTPException(
            status_code=409,
            detail="A pending request already exists for this subject code.",
        ) from exc
    return {**row, "message": "Subject request submitted for administrator review."}

