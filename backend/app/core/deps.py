from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Callable

import psycopg
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.security import decode_access_token
from app.db import get_db


bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    id: str
    role: str
    name: str
    email: str | None = None
    department_id: int | None = None


def _unauthorized(detail: str = "Authentication required.") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    conn: psycopg.Connection = Depends(get_db),
) -> Principal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()
    payload = decode_access_token(credentials.credentials)
    role = payload["role"]
    subject = str(payload["sub"])

    with conn.cursor() as cur:
        if role == "admin":
            cur.execute(
                "SELECT admin_id, name, email, is_active FROM admins WHERE admin_id = %s",
                (subject,),
            )
            row = cur.fetchone()
            if row is None or not row["is_active"]:
                raise _unauthorized("Admin account is not available.")
            return Principal(id=str(row["admin_id"]), role=role, name=row["name"], email=row["email"])
        if role == "faculty":
            cur.execute(
                "SELECT faculty_id, name, email, department_id, status FROM faculty WHERE faculty_id = %s",
                (subject,),
            )
            row = cur.fetchone()
            if row is None:
                raise _unauthorized("Faculty account no longer exists.")
            if row["status"] != "approved":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Faculty account is not approved.",
                )
            return Principal(
                id=str(row["faculty_id"]),
                role=role,
                name=row["name"],
                email=row["email"],
                department_id=row["department_id"],
            )
        cur.execute(
            "SELECT student_id, name, department_id FROM students WHERE student_id = %s",
            (subject,),
        )
        row = cur.fetchone()
        if row is None:
            raise _unauthorized("Student account no longer exists.")
        return Principal(
            id=row["student_id"],
            role=role,
            name=row["name"],
            department_id=row["department_id"],
        )


def require_roles(*roles: str) -> Callable[[Principal], Principal]:
    allowed = set(roles)

    def dependency(current_user: Principal = Depends(get_current_user)) -> Principal:
        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return current_user

    return dependency


admin_required = require_roles("admin")
faculty_required = require_roles("faculty")
student_required = require_roles("student")
authenticated = require_roles("admin", "faculty", "student")


class LoginRateLimiter:
    """A small per-process limiter for authentication endpoints.

    This is deliberately simple and dependency-free. For a multi-worker
    production deployment, back it with Redis or an API gateway limiter.
    """

    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def __call__(self, request: Request) -> None:
        key = f"{client_ip(request)}:{request.url.path}"
        now = time.monotonic()
        window_start = now - settings.login_rate_window_seconds
        bucket = self._hits[key]
        while bucket and bucket[0] < window_start:
            bucket.popleft()
        if len(bucket) >= settings.login_rate_limit:
            retry_after = max(1, int(bucket[0] + settings.login_rate_window_seconds - now))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many sign-in attempts. Please wait and try again.",
                headers={"Retry-After": str(retry_after)},
            )
        bucket.append(now)

    def reset(self, request: Request) -> None:
        key = f"{client_ip(request)}:{request.url.path}"
        self._hits.pop(key, None)


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


login_rate_limiter = LoginRateLimiter()
