from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg import Connection

from app.analytics.service import admin_dashboard, admin_faculty_comparison, faculty_analytics_for_admin, faculty_dashboard, performance_comparison
from app.core.deps import Principal, admin_required, faculty_required
from app.db import get_db


router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/faculty/me")
def my_analytics(
    academic_year: str | None = None,
    semester_number: int | None = Query(default=None, ge=1, le=8),
    subject_code: str | None = None,
    current_user: Principal = Depends(faculty_required),
    conn: Connection = Depends(get_db),
):
    return faculty_dashboard(
        conn,
        int(current_user.id),
        academic_year=academic_year,
        semester_number=semester_number,
        subject_code=subject_code,
    )


@router.get("/faculty/me/comparison")
def my_comparison(
    subject_code: str | None = None,
    current_user: Principal = Depends(faculty_required),
    conn: Connection = Depends(get_db),
):
    return performance_comparison(conn, int(current_user.id), subject_code=subject_code)


@router.get("/admin")
def department_analytics(
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


@router.get("/admin/faculty/{faculty_id}")
def faculty_detail_admin(
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


@router.get("/admin/faculty-comparison")
def faculty_comparison_admin(
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
    }
