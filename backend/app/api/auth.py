from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from psycopg import Connection
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from app.core.deps import Principal, get_current_user, login_rate_limiter
from app.core.security import (
    create_access_token,
    hash_password,
    normalize_email,
    normalize_usn,
    validate_password_strength,
    verify_password,
)
from app.db import get_db
from app.schemas.auth import (
    AdminCreate,
    AdminLogin,
    AdminSetup,
    AuthUser,
    ChangePassword,
    FacultyLogin,
    FacultyRegister,
    StudentLogin,
    StudentRegister,
    TokenResponse,
)
from app.schemas.common import MessageResponse
from app.services.audit import write_audit


router = APIRouter(prefix="/auth", tags=["Authentication"])


def _token_response(subject: str, role: str, name: str, email: str | None = None, department_id: int | None = None, account_status: str | None = None) -> TokenResponse:
    token, expires = create_access_token(subject=subject, role=role)
    return TokenResponse(
        access_token=token,
        expires_at=expires.isoformat(),
        user=AuthUser(
            id=str(subject),
            role=role,
            name=name,
            email=email,
            department_id=department_id,
            status=account_status,
        ),
    )


@router.post("/admin/setup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def setup_first_admin(payload: AdminSetup, conn: Connection = Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS count FROM admins")
        if cur.fetchone()["count"] > 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Initial setup has already been completed. Ask an existing admin to create your account.",
            )
    password_hash = hash_password(payload.password)
    try:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO admins (name, email, password_hash) VALUES (%s, %s, %s) RETURNING admin_id",
                    (payload.name.strip(), normalize_email(payload.email), password_hash),
                )
                admin_id = cur.fetchone()["admin_id"]
    except UniqueViolation as exc:
        raise HTTPException(status_code=409, detail="An admin with this email already exists.") from exc
    return _token_response(str(admin_id), "admin", payload.name.strip(), normalize_email(payload.email))


@router.post("/admin/login", response_model=TokenResponse, dependencies=[Depends(login_rate_limiter)])
def admin_login(payload: AdminLogin, request: Request, conn: Connection = Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT admin_id, name, email, password_hash, is_active FROM admins WHERE email = %s",
            (normalize_email(payload.email),),
        )
        admin = cur.fetchone()
    if admin is None or not admin["is_active"] or not verify_password(payload.password, admin["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    login_rate_limiter.reset(request)
    return _token_response(str(admin["admin_id"]), "admin", admin["name"], admin["email"])


@router.post("/faculty/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def register_faculty(payload: FacultyRegister, conn: Connection = Depends(get_db)):
    password_hash = hash_password(payload.password)
    try:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM departments WHERE id = %s", (payload.department_id,))
                if cur.fetchone() is None:
                    raise HTTPException(status_code=404, detail="Department not found.")
                cur.execute(
                    """
                    INSERT INTO faculty (name, email, password_hash, department_id, status)
                    VALUES (%s, %s, %s, %s, 'pending')
                    """,
                    (payload.name.strip(), normalize_email(payload.email), password_hash, payload.department_id),
                )
    except UniqueViolation as exc:
        raise HTTPException(status_code=409, detail="A faculty account with this email already exists.") from exc
    return MessageResponse(
        message="Registration submitted. An administrator must approve your account before you can sign in."
    )


@router.post("/faculty/login", response_model=TokenResponse, dependencies=[Depends(login_rate_limiter)])
def faculty_login(payload: FacultyLogin, request: Request, conn: Connection = Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT faculty_id, name, email, password_hash, department_id, status FROM faculty WHERE email = %s",
            (normalize_email(payload.email),),
        )
        faculty = cur.fetchone()
    if faculty is None or not verify_password(payload.password, faculty["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    if faculty["status"] == "pending":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your faculty account is awaiting administrator approval.")
    if faculty["status"] != "approved":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your faculty account is not active. Contact the administrator.")
    login_rate_limiter.reset(request)
    return _token_response(
        str(faculty["faculty_id"]),
        "faculty",
        faculty["name"],
        faculty["email"],
        faculty["department_id"],
        faculty["status"],
    )


@router.post("/student/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def register_student(payload: StudentRegister, conn: Connection = Depends(get_db)):
    password_hash = hash_password(payload.password)
    try:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM departments WHERE id = %s", (payload.department_id,))
                if cur.fetchone() is None:
                    raise HTTPException(status_code=404, detail="Department not found.")
                cur.execute(
                    "INSERT INTO students (student_id, name, department_id, password_hash) VALUES (%s, %s, %s, %s)",
                    (normalize_usn(payload.student_id), payload.name.strip(), payload.department_id, password_hash),
                )
    except UniqueViolation as exc:
        raise HTTPException(status_code=409, detail="A student with this USN already exists.") from exc
    return MessageResponse(message="Student account created. You can sign in now.")


@router.post("/student/login", response_model=TokenResponse, dependencies=[Depends(login_rate_limiter)])
def student_login(payload: StudentLogin, request: Request, conn: Connection = Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT student_id, name, department_id, password_hash FROM students WHERE student_id = %s",
            (normalize_usn(payload.student_id),),
        )
        student = cur.fetchone()
    if student is None or not verify_password(payload.password, student["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid USN or password.")
    login_rate_limiter.reset(request)
    return _token_response(
        student["student_id"], "student", student["name"], department_id=student["department_id"]
    )


@router.get("/me", response_model=AuthUser)
def me(current_user: Principal = Depends(get_current_user), conn: Connection = Depends(get_db)):
    account_status = None
    if current_user.role == "faculty":
        with conn.cursor() as cur:
            cur.execute("SELECT status FROM faculty WHERE faculty_id = %s", (current_user.id,))
            row = cur.fetchone()
            account_status = row["status"] if row else None
    return AuthUser(
        id=current_user.id,
        role=current_user.role,
        name=current_user.name,
        email=current_user.email,
        department_id=current_user.department_id,
        status=account_status,
    )


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePassword,
    current_user: Principal = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    validate_password_strength(payload.new_password)
    table, id_column = {
        "admin": ("admins", "admin_id"),
        "faculty": ("faculty", "faculty_id"),
        "student": ("students", "student_id"),
    }[current_user.role]
    with conn.cursor() as cur:
        cur.execute(f"SELECT password_hash FROM {table} WHERE {id_column} = %s", (current_user.id,))
        row = cur.fetchone()
    if row is None or not verify_password(payload.current_password, row["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE {table} SET password_hash = %s WHERE {id_column} = %s",
                (hash_password(payload.new_password), current_user.id),
            )
    return MessageResponse(message="Password changed successfully.")


@router.post("/admins", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def create_admin(
    payload: AdminCreate,
    request: Request,
    current_user: Principal = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required.")
    password_hash = hash_password(payload.password)
    try:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO admins (name, email, password_hash) VALUES (%s, %s, %s) RETURNING admin_id",
                    (payload.name.strip(), normalize_email(payload.email), password_hash),
                )
                admin_id = cur.fetchone()["admin_id"]
            write_audit(
                conn,
                current_user,
                "admin.create",
                entity_type="admin",
                entity_id=admin_id,
                details={"email": normalize_email(payload.email)},
                request=request,
            )
    except UniqueViolation as exc:
        raise HTTPException(status_code=409, detail="An admin with this email already exists.") from exc
    return _token_response(
        str(admin_id), "admin", payload.name.strip(), normalize_email(payload.email), account_status="active"
    )
