"""Faculty feedback-completion tracking.

Completion is computed only from the administrator-maintained class roster in
``student_enrollments``. Registered students are never treated as eligible by
default, and the result contains no ratings, comments, sentiment or feedback
identifiers. Faculty ownership is enforced by requiring an active selection for
the exact subject, academic year and semester.
"""

from __future__ import annotations

from typing import Any

from psycopg import Connection


class CompletionScopeNotFound(Exception):
    """The authenticated faculty member does not teach the requested scope."""


class RosterUnavailable(Exception):
    """No verified roster exists, so a pending list cannot be produced."""


PRIVACY_NOTICE = (
    "Completion status is derived from the administrator-maintained class roster. "
    "It never reveals which student submitted ratings or comments, and it contains "
    "no feedback content or feedback identifiers."
)

METHODOLOGY = (
    "Only active students explicitly enrolled by an administrator for this subject, "
    "academic year and semester are counted. Registered students are not assumed to "
    "be enrolled."
)


def _scope(conn: Connection, faculty_id: int, subject_code: str, academic_year: str, semester_number: int) -> dict[str, Any]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT fss.selection_id, fss.subject_code, s.subject_name,
                   fss.academic_year, fss.semester_number
            FROM faculty_subject_selections fss
            JOIN subjects s ON s.subject_code = fss.subject_code
            WHERE fss.faculty_id = %s
              AND fss.subject_code = %s
              AND fss.academic_year = %s
              AND fss.semester_number = %s
              AND fss.is_active = TRUE
            """,
            (faculty_id, subject_code, academic_year, semester_number),
        )
        selection = cur.fetchone()
    if selection is None:
        raise CompletionScopeNotFound(
            "No active subject selection matches this academic year, semester and subject."
        )
    return selection


def _period(conn: Connection, academic_year: str, semester_number: int) -> dict[str, Any] | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT start_date, end_date,
                   (CURRENT_TIMESTAMP BETWEEN start_date AND end_date) AS is_open
            FROM feedback_periods
            WHERE academic_year = %s AND semester_number = %s
            """,
            (academic_year, semester_number),
        )
        row = cur.fetchone()
    if row is None:
        return None
    return {
        "start_date": row["start_date"].isoformat() if row.get("start_date") else None,
        "end_date": row["end_date"].isoformat() if row.get("end_date") else None,
        "is_open": bool(row.get("is_open")),
    }


def _roster(conn: Connection, subject_code: str, academic_year: str, semester_number: int) -> list[dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT se.student_id, st.name
            FROM student_enrollments se
            JOIN students st ON st.student_id = se.student_id
            WHERE se.subject_code = %s
              AND se.academic_year = %s
              AND se.semester_number = %s
              AND st.is_active = TRUE
            ORDER BY se.student_id
            """,
            (subject_code, academic_year, semester_number),
        )
        return list(cur.fetchall())


def _submitted_student_ids(
    conn: Connection,
    faculty_id: int,
    subject_code: str,
    academic_year: str,
    semester_number: int,
) -> set[str]:
    """Students on this scope's roster who have submitted to this faculty member.

    The join is deliberately limited to the authenticated faculty member's own
    offering, so another faculty member teaching the same subject cannot change
    this result.
    """

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT fb.student_id
            FROM feedback fb
            JOIN course_offerings co ON co.offering_id = fb.offering_id
            JOIN student_enrollments se
              ON se.student_id = fb.student_id
             AND se.subject_code = co.subject_code
             AND se.academic_year = co.academic_year
             AND se.semester_number = co.semester_number
            WHERE co.faculty_id = %s
              AND co.subject_code = %s
              AND co.academic_year = %s
              AND co.semester_number = %s
            """,
            (faculty_id, subject_code, academic_year, semester_number),
        )
        return {row["student_id"] for row in cur.fetchall()}


def get_completion(
    conn: Connection,
    faculty_id: int,
    *,
    subject_code: str,
    academic_year: str,
    semester_number: int,
) -> dict[str, Any]:
    """Return completion counts and the pending list for one owned scope.

    Raises ``CompletionScopeNotFound`` when the faculty member does not teach the
    scope. The pending list is always empty when no verified roster exists; callers
    that need a report must check ``roster_available`` first.
    """

    scope = _scope(conn, faculty_id, subject_code, academic_year, semester_number)
    roster = _roster(conn, subject_code, academic_year, semester_number)
    submitted_ids = _submitted_student_ids(
        conn, faculty_id, subject_code, academic_year, semester_number
    )

    roster_ids = {row["student_id"] for row in roster}
    submitted_ids &= roster_ids
    pending = [row for row in roster if row["student_id"] not in submitted_ids]

    eligible_count = len(roster)
    submitted_count = len(submitted_ids)
    pending_count = len(pending)
    percentage = round((submitted_count / eligible_count) * 100, 1) if eligible_count else 0.0

    return {
        "subject_code": scope["subject_code"],
        "subject_name": scope["subject_name"],
        "academic_year": scope["academic_year"],
        "semester_number": scope["semester_number"],
        "period": _period(conn, academic_year, semester_number),
        "roster_available": eligible_count > 0,
        "eligible_count": eligible_count,
        "submitted_count": submitted_count,
        "pending_count": pending_count,
        "completion_percentage": percentage,
        "pending_students": pending,
        "privacy_notice": PRIVACY_NOTICE,
        "methodology": METHODOLOGY,
    }
