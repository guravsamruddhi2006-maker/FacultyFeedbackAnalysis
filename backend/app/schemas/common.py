from __future__ import annotations

import re
from typing import Annotated

from pydantic import AfterValidator, BaseModel


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USN_RE = re.compile(r"^[A-Za-z0-9]{6,50}$")


def _email(value: str) -> str:
    value = value.strip().lower()
    if not EMAIL_RE.match(value):
        raise ValueError("Enter a valid email address.")
    return value


def _usn(value: str) -> str:
    value = value.strip().upper()
    if not USN_RE.match(value):
        raise ValueError("USN must be 6-50 letters or digits.")
    return value


Email = Annotated[str, AfterValidator(_email)]
USN = Annotated[str, AfterValidator(_usn)]


class MessageResponse(BaseModel):
    message: str


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
