from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import psycopg

from app.analytics.text import (
    analyze_comments,
    classify_topics,
    extract_keywords,
    predict_sentiment,
)
from app.services.insights import build_insights, build_trend_insights


def _conditions(
    *,
    academic_year: str | None = None,
    semester_number: int | None = None,
    subject_code: str | None = None,
    faculty_id: int | None = None,
) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []
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
    return (" AND ".join(clauses) if clauses else "TRUE"), params


def _rows(conn: psycopg.Connection, sql: str, params: list[Any] | tuple[Any, ...]) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(sql, tuple(params))
        return list(cur.fetchall())


def _row(conn: psycopg.Connection, sql: str, params: list[Any] | tuple[Any, ...]) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(sql, tuple(params))
        return cur.fetchone()


def get_filter_options(conn: psycopg.Connection, *, faculty_id: int | None = None) -> dict[str, Any]:
    scope = "WHERE co.faculty_id = %s" if faculty_id else ""
    params: tuple[Any, ...] = (faculty_id,) if faculty_id else ()
    years = _rows(
        conn,
        f"SELECT DISTINCT co.academic_year FROM course_offerings co {scope} ORDER BY co.academic_year DESC",
        params,
    )
    semesters = _rows(
        conn,
        f"SELECT DISTINCT co.semester_number FROM course_offerings co {scope} ORDER BY co.semester_number",
        params,
    )
    subjects = _rows(
        conn,
        f"""
        SELECT DISTINCT co.subject_code, s.subject_name
        FROM course_offerings co JOIN subjects s ON s.subject_code = co.subject_code
        {scope}
        ORDER BY co.subject_code
        """,
        params,
    )
    if faculty_id:
        faculty: list[dict] = []
    else:
        faculty = _rows(
            conn,
            "SELECT faculty_id, name FROM faculty WHERE status = 'approved' ORDER BY name",
            (),
        )
    return {
        "academic_years": [row["academic_year"] for row in years],
        "semesters": [row["semester_number"] for row in semesters],
        "subjects": subjects,
        "faculty": faculty,
    }


def _question_stats(
    conn: psycopg.Connection,
    *,
    faculty_id: int | None = None,
    academic_year: str | None = None,
    semester_number: int | None = None,
    subject_code: str | None = None,
) -> list[dict]:
    where, params = _conditions(
        academic_year=academic_year,
        semester_number=semester_number,
        subject_code=subject_code,
        faculty_id=faculty_id,
    )
    rows = _rows(
        conn,
        f"""
        SELECT fq.question_id, fq.question_text,
               ROUND(COALESCE(AVG(fa.rating), 0)::numeric, 2) AS average_rating,
               COUNT(fa.rating)::int AS response_count
        FROM feedback_questions fq
        LEFT JOIN (
            SELECT fa.question_id, fa.rating
            FROM feedback_answer fa
            JOIN feedback fb ON fb.feedback_id = fa.feedback_id
            JOIN course_offerings co ON co.offering_id = fb.offering_id
            WHERE {where}
        ) fa ON fa.question_id = fq.question_id
        WHERE fq.is_active = TRUE
        GROUP BY fq.question_id, fq.question_text
        ORDER BY fq.question_id
        """,
        params,
    )
    return [
        {
            "question_id": row["question_id"],
            "question_text": row["question_text"],
            "average_rating": float(row["average_rating"]),
            "response_count": row["response_count"],
        }
        for row in rows
    ]


def _rating_distribution(
    conn: psycopg.Connection,
    *,
    faculty_id: int | None = None,
    academic_year: str | None = None,
    semester_number: int | None = None,
    subject_code: str | None = None,
) -> list[dict]:
    where, params = _conditions(
        academic_year=academic_year,
        semester_number=semester_number,
        subject_code=subject_code,
        faculty_id=faculty_id,
    )
    rows = _rows(
        conn,
        f"""
        SELECT fa.rating, COUNT(*)::int AS count
        FROM feedback_answer fa
        JOIN feedback fb ON fb.feedback_id = fa.feedback_id
        JOIN course_offerings co ON co.offering_id = fb.offering_id
        WHERE {where}
        GROUP BY fa.rating
        ORDER BY fa.rating
        """,
        params,
    )
    counts = {int(row["rating"]): row["count"] for row in rows}
    total = sum(counts.values())
    labels = {1: "Very Poor", 2: "Poor", 3: "Average", 4: "Good", 5: "Excellent"}
    return [
        {
            "rating": rating,
            "label": labels[rating],
            "count": counts.get(rating, 0),
            "percentage": round(100 * counts.get(rating, 0) / total, 1) if total else 0.0,
        }
        for rating in range(1, 6)
    ]


def _comments(
    conn: psycopg.Connection,
    *,
    faculty_id: int | None = None,
    academic_year: str | None = None,
    semester_number: int | None = None,
    subject_code: str | None = None,
    limit: int = 250,
) -> list[dict]:
    where, params = _conditions(
        academic_year=academic_year,
        semester_number=semester_number,
        subject_code=subject_code,
        faculty_id=faculty_id,
    )
    rows = _rows(
        conn,
        f"""
        SELECT fb.feedback_id, fb.comment, fb.submitted_at,
               co.academic_year, co.semester_number, co.subject_code,
               s.subject_name
        FROM feedback fb
        JOIN course_offerings co ON co.offering_id = fb.offering_id
        JOIN subjects s ON s.subject_code = co.subject_code
        WHERE {where} AND fb.comment IS NOT NULL AND trim(fb.comment) <> ''
        ORDER BY fb.submitted_at DESC
        LIMIT %s
        """,
        params + [limit],
    )
    for row in rows:
        row["sentiment"] = predict_sentiment(row["comment"])
        row["submitted_at"] = row["submitted_at"].isoformat()
    return rows


def _subject_summary(
    conn: psycopg.Connection,
    *,
    faculty_id: int,
    academic_year: str | None,
    semester_number: int | None,
    subject_code: str | None,
) -> list[dict]:
    where, params = _conditions(
        academic_year=academic_year,
        semester_number=semester_number,
        subject_code=subject_code,
        faculty_id=faculty_id,
    )
    rows = _rows(
        conn,
        f"""
        SELECT co.subject_code, s.subject_name, co.semester_number,
               ROUND(COALESCE(AVG(fa.rating), 0)::numeric, 2) AS average_rating,
               COUNT(DISTINCT fb.feedback_id)::int AS response_count,
               COUNT(DISTINCT co.offering_id)::int AS offering_count
        FROM course_offerings co
        JOIN subjects s ON s.subject_code = co.subject_code
        LEFT JOIN feedback fb ON fb.offering_id = co.offering_id
        LEFT JOIN feedback_answer fa ON fa.feedback_id = fb.feedback_id
        WHERE {where}
        GROUP BY co.subject_code, s.subject_name, co.semester_number
        ORDER BY co.subject_code
        """,
        params,
    )
    return [{**row, "average_rating": float(row["average_rating"])} for row in rows]


def _trend(
    conn: psycopg.Connection,
    *,
    faculty_id: int,
    semester_number: int | None,
    subject_code: str | None,
) -> list[dict]:
    where, params = _conditions(
        semester_number=semester_number,
        subject_code=subject_code,
        faculty_id=faculty_id,
    )
    rows = _rows(
        conn,
        f"""
        SELECT co.academic_year,
               ROUND(COALESCE(AVG(fa.rating), 0)::numeric, 2) AS average_rating,
               COUNT(DISTINCT fb.feedback_id)::int AS response_count
        FROM course_offerings co
        LEFT JOIN feedback fb ON fb.offering_id = co.offering_id
        LEFT JOIN feedback_answer fa ON fa.feedback_id = fb.feedback_id
        WHERE {where}
        GROUP BY co.academic_year
        ORDER BY co.academic_year
        """,
        params,
    )
    return [{**row, "average_rating": float(row["average_rating"])} for row in rows]


def _evidence_insights(question_rows: list[dict]) -> tuple[list[dict], list[dict]]:
    strengths: list[dict] = []
    improvements: list[dict] = []
    for row in question_rows:
        count = row["response_count"]
        average = row["average_rating"]
        if count >= 3 and average >= 4.0:
            strengths.append(
                {
                    "title": row["question_text"].rstrip("."),
                    "evidence": f"{average:.2f}/5 average from {count} ratings.",
                    "average_rating": average,
                    "response_count": count,
                }
            )
        elif count >= 3 and average <= 3.0:
            improvements.append(
                {
                    "title": row["question_text"].rstrip("."),
                    "evidence": f"{average:.2f}/5 average from {count} ratings.",
                    "average_rating": average,
                    "response_count": count,
                }
            )
    strengths.sort(key=lambda item: (-item["average_rating"], -item["response_count"]))
    improvements.sort(key=lambda item: (item["average_rating"], -item["response_count"]))
    return strengths, improvements


def _sentiment_block(comments: list[dict]) -> dict[str, Any]:
    raw_comments = [row["comment"] for row in comments]
    return {
        "summary": analyze_comments(raw_comments),
        "positive_comments": [row for row in comments if row["sentiment"]["label"] == "positive"][:20],
        "negative_comments": [row for row in comments if row["sentiment"]["label"] == "negative"][:20],
        "topics": classify_topics(raw_comments),
        "keywords": extract_keywords(raw_comments),
    }


def get_my_faculty_id(conn: psycopg.Connection, faculty_id: int) -> dict | None:
    return _row(
        conn,
        "SELECT faculty_id, name, email, department_id, status FROM faculty WHERE faculty_id = %s",
        [faculty_id],
    )


def faculty_dashboard(
    conn: psycopg.Connection,
    faculty_id: int,
    *,
    academic_year: str | None = None,
    semester_number: int | None = None,
    subject_code: str | None = None,
) -> dict[str, Any]:
    where, params = _conditions(
        academic_year=academic_year,
        semester_number=semester_number,
        subject_code=subject_code,
        faculty_id=faculty_id,
    )
    overall = _row(
        conn,
        f"""
        SELECT COUNT(DISTINCT fb.feedback_id)::int AS response_count,
               ROUND(COALESCE(AVG(fa.rating), 0)::numeric, 2) AS average_rating
        FROM course_offerings co
        LEFT JOIN feedback fb ON fb.offering_id = co.offering_id
        LEFT JOIN feedback_answer fa ON fa.feedback_id = fb.feedback_id
        WHERE {where}
        """,
        params,
    ) or {"response_count": 0, "average_rating": 0}
    question_rows = _question_stats(
        conn,
        faculty_id=faculty_id,
        academic_year=academic_year,
        semester_number=semester_number,
        subject_code=subject_code,
    )
    comments = _comments(
        conn,
        faculty_id=faculty_id,
        academic_year=academic_year,
        semester_number=semester_number,
        subject_code=subject_code,
    )
    strengths, improvements = _evidence_insights(question_rows)
    trend_rows = _trend(conn, faculty_id=faculty_id, semester_number=semester_number, subject_code=subject_code)
    insights = build_insights(
        question_rows=question_rows,
        comments=comments,
        overall_average=float(overall["average_rating"]),
        response_count=overall["response_count"],
    )
    insights["generated_at"] = datetime.now(timezone.utc).isoformat()
    return {
        "faculty_id": faculty_id,
        "filters": {
            "academic_year": academic_year,
            "semester_number": semester_number,
            "subject_code": subject_code,
        },
        "overall": {
            "average_rating": float(overall["average_rating"]),
            "response_count": overall["response_count"],
        },
        "question_stats": question_rows,
        "rating_distribution": _rating_distribution(
            conn,
            faculty_id=faculty_id,
            academic_year=academic_year,
            semester_number=semester_number,
            subject_code=subject_code,
        ),
        "subject_summary": _subject_summary(
            conn,
            faculty_id=faculty_id,
            academic_year=academic_year,
            semester_number=semester_number,
            subject_code=subject_code,
        ),
        "trend": trend_rows,
        "comments": comments,
        "strengths": strengths,
        "improvement_areas": improvements,
        "insights": insights,
        "trend_insights": build_trend_insights(trend_rows),
        "sentiment": _sentiment_block(comments),
        "filter_options": get_filter_options(conn, faculty_id=faculty_id),
        "privacy_notice": "All feedback is anonymous. Student identifiers are never returned by faculty endpoints.",
    }


def performance_comparison(
    conn: psycopg.Connection,
    faculty_id: int,
    *,
    subject_code: str | None = None,
) -> dict[str, Any]:
    where, params = _conditions(faculty_id=faculty_id, subject_code=subject_code)
    rows = _rows(
        conn,
        f"""
        SELECT co.academic_year, co.subject_code, s.subject_name,
               ROUND(COALESCE(AVG(fa.rating), 0)::numeric, 2) AS average_rating,
               COUNT(DISTINCT fb.feedback_id)::int AS response_count
        FROM course_offerings co
        JOIN subjects s ON s.subject_code = co.subject_code
        LEFT JOIN feedback fb ON fb.offering_id = co.offering_id
        LEFT JOIN feedback_answer fa ON fa.feedback_id = fb.feedback_id
        WHERE {where}
        GROUP BY co.academic_year, co.subject_code, s.subject_name
        ORDER BY co.academic_year, co.subject_code
        """,
        params,
    )
    comparison = [{**row, "average_rating": float(row["average_rating"])} for row in rows]
    delta = None
    direction = "insufficient_data"
    if len(comparison) >= 2 and comparison[0]["response_count"] and comparison[-1]["response_count"]:
        delta = round(comparison[-1]["average_rating"] - comparison[0]["average_rating"], 2)
        direction = "improving" if delta > 0.05 else "declining" if delta < -0.05 else "stable"
    return {
        "faculty_id": faculty_id,
        "subject_code": subject_code,
        "comparison": comparison,
        "delta": delta,
        "direction": direction,
        "note": "This compares one faculty member with their own earlier offerings, never two different people.",
    }


def faculty_performance_overview(
    conn: psycopg.Connection,
    *,
    academic_year: str | None = None,
    semester_number: int | None = None,
    subject_code: str | None = None,
    faculty_id: int | None = None,
) -> list[dict]:
    where, params = _conditions(
        academic_year=academic_year,
        semester_number=semester_number,
        subject_code=subject_code,
        faculty_id=faculty_id,
    )
    rows = _rows(
        conn,
        f"""
        SELECT f.faculty_id, f.name, f.email,
               COUNT(DISTINCT co.offering_id)::int AS offering_count,
               COUNT(DISTINCT fb.feedback_id)::int AS response_count,
               ROUND(COALESCE(AVG(fa.rating), 0)::numeric, 2) AS average_rating
        FROM faculty f
        JOIN course_offerings co ON co.faculty_id = f.faculty_id
        LEFT JOIN feedback fb ON fb.offering_id = co.offering_id
        LEFT JOIN feedback_answer fa ON fa.feedback_id = fb.feedback_id
        WHERE {where}
        GROUP BY f.faculty_id, f.name, f.email
        ORDER BY average_rating DESC, f.name
        """,
        params,
    )
    return [{**row, "average_rating": float(row["average_rating"])} for row in rows]


def admin_dashboard(
    conn: psycopg.Connection,
    *,
    academic_year: str | None = None,
    semester_number: int | None = None,
    subject_code: str | None = None,
    faculty_id: int | None = None,
) -> dict[str, Any]:
    where, params = _conditions(
        academic_year=academic_year,
        semester_number=semester_number,
        subject_code=subject_code,
        faculty_id=faculty_id,
    )
    counts = _row(
        conn,
        """
        SELECT
          (SELECT COUNT(*) FROM students)::int AS total_students,
          (SELECT COUNT(*) FROM faculty)::int AS total_faculty,
          (SELECT COUNT(*) FROM faculty WHERE status = 'pending')::int AS pending_faculty,
          (SELECT COUNT(*) FROM subjects)::int AS total_subjects,
          (SELECT COUNT(*) FROM course_offerings)::int AS total_course_offerings,
          (SELECT COUNT(*) FROM admins WHERE is_active = TRUE)::int AS active_admins,
          (SELECT COUNT(*) FROM feedback_periods
             WHERE CURRENT_TIMESTAMP BETWEEN start_date AND end_date)::int AS active_feedback_periods
        """,
        [],
    ) or {}
    scope = _row(
        conn,
        f"""
        SELECT COUNT(DISTINCT co.offering_id)::int AS offering_count,
               COUNT(DISTINCT fb.feedback_id)::int AS feedback_count,
               ROUND(COALESCE(AVG(fa.rating), 0)::numeric, 2) AS average_rating
        FROM course_offerings co
        LEFT JOIN feedback fb ON fb.offering_id = co.offering_id
        LEFT JOIN feedback_answer fa ON fa.feedback_id = fb.feedback_id
        WHERE {where}
        """,
        params,
    ) or {"offering_count": 0, "feedback_count": 0, "average_rating": 0}
    total_students = counts.get("total_students", 0)
    offering_count = scope.get("offering_count", 0)
    feedback_count = scope.get("feedback_count", 0)
    denominator = max(total_students * offering_count, 1)
    comments = _comments(
        conn,
        academic_year=academic_year,
        semester_number=semester_number,
        subject_code=subject_code,
        faculty_id=faculty_id,
    )
    question_rows = _question_stats(
        conn,
        academic_year=academic_year,
        semester_number=semester_number,
        subject_code=subject_code,
        faculty_id=faculty_id,
    )
    _, improvements = _evidence_insights(question_rows)
    sentiment = _sentiment_block(comments)
    insights = build_insights(
        question_rows=question_rows,
        comments=comments,
        overall_average=float(scope.get("average_rating") or 0),
        response_count=scope.get("feedback_count") or 0,
    )
    insights["generated_at"] = datetime.now(timezone.utc).isoformat()

    semester_rows = _rows(
        conn,
        f"""
        SELECT co.semester_number,
               COUNT(DISTINCT fb.feedback_id)::int AS response_count,
               ROUND(COALESCE(AVG(fa.rating), 0)::numeric, 2) AS average_rating
        FROM course_offerings co
        LEFT JOIN feedback fb ON fb.offering_id = co.offering_id
        LEFT JOIN feedback_answer fa ON fa.feedback_id = fb.feedback_id
        WHERE {where}
        GROUP BY co.semester_number
        ORDER BY co.semester_number
        """,
        params,
    )
    year_where, year_params = _conditions(
        semester_number=semester_number,
        subject_code=subject_code,
        faculty_id=faculty_id,
    )
    year_rows = _rows(
        conn,
        f"""
        SELECT co.academic_year,
               COUNT(DISTINCT fb.feedback_id)::int AS response_count,
               ROUND(COALESCE(AVG(fa.rating), 0)::numeric, 2) AS average_rating
        FROM course_offerings co
        LEFT JOIN feedback fb ON fb.offering_id = co.offering_id
        LEFT JOIN feedback_answer fa ON fa.feedback_id = fb.feedback_id
        WHERE {year_where}
        GROUP BY co.academic_year
        ORDER BY co.academic_year
        """,
        year_params,
    )

    return {
        "filters": {
            "academic_year": academic_year,
            "semester_number": semester_number,
            "subject_code": subject_code,
            "faculty_id": faculty_id,
        },
        "counts": {**counts, **scope},
        "submission_rate": round(100 * feedback_count / denominator, 1),
        "submission_rate_note": "Feedback records divided by (students × filtered course offerings). This is a coverage indicator.",
        "faculty_performance": faculty_performance_overview(
            conn,
            academic_year=academic_year,
            semester_number=semester_number,
            subject_code=subject_code,
            faculty_id=faculty_id,
        ),
        "semester_analytics": [{**row, "average_rating": float(row["average_rating"])} for row in semester_rows],
        "academic_year_comparison": [{**row, "average_rating": float(row["average_rating"])} for row in year_rows],
        "question_stats": question_rows,
        "improvement_areas": improvements,
        "insights": insights,
        "sentiment": sentiment,
        "filter_options": get_filter_options(conn),
        "privacy_notice": "Aggregates only. Student identities are not included in analytics or exports.",
    }


def faculty_analytics_for_admin(
    conn: psycopg.Connection,
    faculty_id: int,
    *,
    academic_year: str | None = None,
    semester_number: int | None = None,
    subject_code: str | None = None,
) -> dict[str, Any]:
    faculty = get_my_faculty_id(conn, faculty_id)
    if faculty is None:
        raise KeyError("Faculty not found")
    data = faculty_dashboard(
        conn,
        faculty_id,
        academic_year=academic_year,
        semester_number=semester_number,
        subject_code=subject_code,
    )
    data["faculty"] = faculty
    return data


def admin_faculty_comparison(
    conn: psycopg.Connection,
    *,
    subject_code: str,
    academic_year: str | None = None,
    semester_number: int | None = None,
) -> list[dict]:
    return faculty_performance_overview(
        conn,
        academic_year=academic_year,
        semester_number=semester_number,
        subject_code=subject_code,
    )
