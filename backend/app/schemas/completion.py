from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import USN


def _subject_code(value: str) -> str:
    return value.strip().upper()


class EnrollmentCreate(BaseModel):
    student_id: USN
    subject_code: str = Field(min_length=2, max_length=20)
    academic_year: str = Field(pattern=r"^[0-9]{4}-[0-9]{2}$")
    semester_number: int = Field(ge=1, le=8)

    @field_validator("subject_code")
    @classmethod
    def uppercase_subject(cls, value: str) -> str:
        return _subject_code(value)


class EnrollmentBulkCreate(BaseModel):
    student_ids: list[USN] = Field(min_length=1, max_length=500)
    subject_code: str = Field(min_length=2, max_length=20)
    academic_year: str = Field(pattern=r"^[0-9]{4}-[0-9]{2}$")
    semester_number: int = Field(ge=1, le=8)

    @field_validator("subject_code")
    @classmethod
    def uppercase_subject(cls, value: str) -> str:
        return _subject_code(value)
