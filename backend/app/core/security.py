from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from fastapi import HTTPException, status

from app.core.config import settings


PASSWORD_MIN = 8
PASSWORD_MAX_BYTES = 72


def validate_password_strength(password: str) -> None:
    if len(password) < PASSWORD_MIN:
        raise HTTPException(status_code=422, detail=f"Password must be at least {PASSWORD_MIN} characters.")
    if len(password.encode("utf-8")) > PASSWORD_MAX_BYTES:
        raise HTTPException(status_code=422, detail="Password must be at most 72 UTF-8 bytes.")
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise HTTPException(
            status_code=422,
            detail="Password must include at least one letter and one number.",
        )


def hash_password(password: str) -> str:
    validate_password_strength(password)
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str | None) -> bool:
    if not hashed_password:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(subject: str, role: str) -> tuple[str, datetime]:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=settings.access_token_minutes)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": expires,
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expires


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "role", "exp"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    if payload.get("role") not in {"admin", "faculty", "student"}:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid role.")
    return payload


def normalize_email(email: str) -> str:
    return email.strip().lower()


def normalize_usn(usn: str) -> str:
    return usn.strip().upper()
