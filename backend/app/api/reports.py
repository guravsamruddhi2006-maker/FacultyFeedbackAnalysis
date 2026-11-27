from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from psycopg import Connection

from app.core.deps import Principal, admin_required, faculty_required
from app.db import get_db
from app.services.completion_service import CompletionScopeNotFound, RosterUnavailable
from app.services.report_service import (
    build_admin_report,
    build_completion_report,
    build_faculty_report,
)


router = APIRouter(prefix="/reports", tags=["Reports"])


def _response(content: bytes, media_type: str, filename: str) -> Response:
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


@router.get("/faculty/me")
def faculty_report(
    format: str = Query(default="pdf", pattern="^(csv|pdf)$"),
    academic_year: str | None = None,
    semester_number: int | None = Query(default=None, ge=1, le=8),
    subject_code: str | None = None,
    current_user: Principal = Depends(faculty_required),
    conn: Connection = Depends(get_db),
):
    with conn.cursor() as cur:
        cur.execute("SELECT faculty_id, name, email FROM faculty WHERE faculty_id = %s", (current_user.id,))
        faculty = cur.fetchone() or {"faculty_id": int(current_user.id), "name": current_user.name}
    content, media_type, filename = build_faculty_report(
        conn,
        int(current_user.id),
        academic_year=academic_year,
        semester_number=semester_number,
        subject_code=subject_code,
        fmt=format,
    )
    # The report builder re-queries the profile for the heading; ensure a name is present.
    _ = faculty
    return _response(content, media_type, filename)


@router.get("/faculty/me/completion")
def faculty_completion_report(
    format: str = Query(default="pdf", pattern="^pdf$"),
    subject_code: str = Query(min_length=2, max_length=20),
    academic_year: str = Query(pattern=r"^[0-9]{4}-[0-9]{2}$"),
    semester_number: int = Query(ge=1, le=8),
    current_user: Principal = Depends(faculty_required),
    conn: Connection = Depends(get_db),
):
    """Download the pending-student PDF for one owned subject and period."""
    try:
        content, media_type, filename = build_completion_report(
            conn,
            int(current_user.id),
            subject_code=subject_code.strip().upper(),
            academic_year=academic_year,
            semester_number=semester_number,
        )
    except CompletionScopeNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RosterUnavailable as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    _ = format
    return _response(content, media_type, filename)


@router.get("/admin")
def admin_report(
    format: str = Query(default="pdf", pattern="^(csv|pdf)$"),
    academic_year: str | None = None,
    semester_number: int | None = Query(default=None, ge=1, le=8),
    subject_code: str | None = None,
    faculty_id: int | None = None,
    _: Principal = Depends(admin_required),
    conn: Connection = Depends(get_db),
):
    content, media_type, filename = build_admin_report(
        conn,
        academic_year=academic_year,
        semester_number=semester_number,
        subject_code=subject_code,
        faculty_id=faculty_id,
        fmt=format,
    )
    return _response(content, media_type, filename)
