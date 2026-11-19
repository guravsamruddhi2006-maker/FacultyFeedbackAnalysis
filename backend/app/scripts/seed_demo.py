"""Seed clearly fictional demo data for local evaluation.

Usage:
    python -m app.scripts.seed_demo
    python -m app.scripts.seed_demo --with-feedback
"""

from __future__ import annotations

import argparse
from datetime import datetime

from app.core.security import hash_password, normalize_email, normalize_usn
from app.db import db_transaction


DEMO_PASSWORD = "Demo@12345"
ADMIN_PASSWORD = "Admin@12345"

FACULTY = [
    ("Dr. Ravi Kumar", "ravi.demo@facultyinsight.local"),
    ("Dr. Priya Sharma", "priya.demo@facultyinsight.local"),
    ("Dr. Kumar Rao", "kumar.demo@facultyinsight.local"),
]

COMMENTS = [
    ("Explains every concept with clarity and patience. The practical examples made the subject easy to understand.", 5),
    ("Excellent subject knowledge and very supportive during doubts. Classroom discussions are engaging.", 5),
    ("Classes are useful and well planned. More real-world case studies would make them even better.", 4),
    ("The syllabus was completed on time. The pace was slightly fast in the middle of the semester.", 3),
    ("Sometimes the explanation moves too quickly. Additional examples would help students who are new to the topic.", 2),
    ("Very interactive sessions and the teacher encourages everyone to participate. I learned a lot.", 5),
    ("The subject is interesting but the lectures can become monotonous. Please include more demonstrations.", 2),
    ("Good teaching and clear notes. Assignments helped me understand the concepts better.", 4),
    ("The faculty is knowledgeable, but response to online doubts was delayed during the project week.", 3),
    ("Well organized classes with useful practical examples. Thank you for the support throughout the semester.", 5),
]


def _get_or_create_faculty(conn, name: str, email: str) -> int:
    email = normalize_email(email)
    with conn.cursor() as cur:
        cur.execute("SELECT faculty_id FROM faculty WHERE email = %s", (email,))
        row = cur.fetchone()
        if row:
            return row["faculty_id"]
        cur.execute("SELECT id FROM departments WHERE code = 'CSE'")
        department = cur.fetchone()
        cur.execute(
            """
            INSERT INTO faculty (name, email, password_hash, department_id, status)
            VALUES (%s, %s, %s, %s, 'approved') RETURNING faculty_id
            """,
            (name, email, hash_password(DEMO_PASSWORD), department["id"]),
        )
        return cur.fetchone()["faculty_id"]


def _get_or_create_offering(conn, year: str, semester: int, subject: str, faculty_id: int) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO course_offerings (academic_year, semester_number, subject_code, faculty_id)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (academic_year, semester_number, subject_code, faculty_id)
            DO NOTHING
            RETURNING offering_id
            """,
            (year, semester, subject, faculty_id),
        )
        row = cur.fetchone()
        if row:
            return row["offering_id"]
        cur.execute(
            """
            SELECT offering_id FROM course_offerings
            WHERE academic_year = %s AND semester_number = %s AND subject_code = %s AND faculty_id = %s
            """,
            (year, semester, subject, faculty_id),
        )
        return cur.fetchone()["offering_id"]


def _seed_feedback(conn, offering_ids: list[tuple[int, int]]) -> None:
    """offering_ids: list of (offering_id, faculty_offset)."""
    with conn.cursor() as cur:
        cur.execute("SELECT question_id FROM feedback_questions WHERE is_active = TRUE ORDER BY question_id")
        questions = [row["question_id"] for row in cur.fetchall()]
        cur.execute("SELECT id FROM departments WHERE code = 'CSE'")
        department_id = cur.fetchone()["id"]
        for index in range(1, 16):
            student_id = normalize_usn(f"4UB26CS{index:03d}")
            cur.execute(
                """
                INSERT INTO students (student_id, name, department_id, password_hash)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (student_id) DO NOTHING
                """,
                (student_id, f"Demo Student {index:02d}", department_id, hash_password(DEMO_PASSWORD)),
            )
        for offering_index, (offering_id, offset) in enumerate(offering_ids):
            for student_index in range(1, 13):
                student_id = normalize_usn(f"4UB26CS{student_index:03d}")
                comment, base_rating = COMMENTS[(student_index + offering_index + offset) % len(COMMENTS)]
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT feedback_id FROM feedback WHERE student_id = %s AND offering_id = %s",
                        (student_id, offering_id),
                    )
                    if cur.fetchone():
                        continue
                    cur.execute(
                        "INSERT INTO feedback (student_id, offering_id, comment, submitted_at) VALUES (%s, %s, %s, %s) RETURNING feedback_id",
                        (student_id, offering_id, comment, datetime.now()),
                    )
                    feedback_id = cur.fetchone()["feedback_id"]
                    for q_index, question_id in enumerate(questions):
                        rating = max(1, min(5, base_rating + ((student_index + q_index + offset) % 3) - 1))
                        cur.execute(
                            "INSERT INTO feedback_answer (feedback_id, question_id, rating) VALUES (%s, %s, %s)",
                            (feedback_id, question_id, rating),
                        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed fictional demo accounts and feedback.")
    parser.add_argument("--with-feedback", action="store_true", help="Also generate demo offerings and feedback")
    args = parser.parse_args()

    with db_transaction() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT admin_id FROM admins WHERE email = %s", ("admin@facultyinsight.local",))
            if cur.fetchone() is None:
                cur.execute(
                    "INSERT INTO admins (name, email, password_hash) VALUES (%s, %s, %s)",
                    ("Demo Administrator", "admin@facultyinsight.local", hash_password(ADMIN_PASSWORD)),
                )
        faculty_ids = [_get_or_create_faculty(conn, name, email) for name, email in FACULTY]
        if args.with_feedback:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO feedback_periods (academic_year, semester_number, start_date, end_date)
                    VALUES ('2026-27', 5, '2026-01-01', '2027-12-31')
                    ON CONFLICT (academic_year, semester_number) DO NOTHING
                    """
                )
                cur.execute(
                    """
                    INSERT INTO feedback_periods (academic_year, semester_number, start_date, end_date)
                    VALUES ('2027-28', 5, '2027-01-01', '2027-06-30')
                    ON CONFLICT (academic_year, semester_number) DO NOTHING
                    """
                )
            offerings = [
                (_get_or_create_offering(conn, "2026-27", 5, "BCS501", faculty_ids[0]), 0),
                (_get_or_create_offering(conn, "2026-27", 5, "BCS501", faculty_ids[1]), 1),
                (_get_or_create_offering(conn, "2026-27", 5, "BCS502", faculty_ids[2]), 2),
                (_get_or_create_offering(conn, "2027-28", 5, "BCS501", faculty_ids[0]), 3),
            ]
            _seed_feedback(conn, offerings)

    print("Demo seed complete.")
    print("Admin:   admin@facultyinsight.local / Admin@12345")
    print("Faculty: ravi.demo@facultyinsight.local / Demo@12345")
    print("         priya.demo@facultyinsight.local / Demo@12345")
    print("Student: 4UB26CS001 / Demo@12345")


if __name__ == "__main__":
    main()
