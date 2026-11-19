from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg import Connection

from app.analytics.service import (
    faculty_dashboard as build_faculty_dashboard,
    get_filter_options,
    get_my_faculty_id,
    performance_comparison,
)
from app.analytics.text import analyze_comments, classify_topics, extract_keywords, predict_sentiment
from app.core.deps import Principal, faculty_required
from app.db import get_db


router = APIRouter(prefix="/faculty/me", tags=["Faculty"])


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
