from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class FacultySelectionBase(BaseModel):
    subject_code: str = Field(min_length=2, max_length=20)
    academic_year: str = Field(pattern=r"^[0-9]{4}-[0-9]{2}$")
    semester_number: int = Field(ge=1, le=8)

    @field_validator("subject_code")
    @classmethod
    def uppercase_code(cls, value: str) -> str:
        return value.strip().upper()


class FacultySelectionCreate(FacultySelectionBase):
    pass


class FacultySelectionUpdate(FacultySelectionBase):
    pass


class SubjectRequestCreate(BaseModel):
    subject_code: str = Field(min_length=2, max_length=20)
    subject_name: str = Field(min_length=3, max_length=180)
    semester_number: int = Field(ge=1, le=8)

    @field_validator("subject_code")
    @classmethod
    def uppercase_code(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("subject_name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return value.strip()
