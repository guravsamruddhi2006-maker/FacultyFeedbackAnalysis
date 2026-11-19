from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.common import Email, USN


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    code: str = Field(min_length=2, max_length=10)

    @field_validator("code")
    @classmethod
    def uppercase_code(cls, value: str) -> str:
        return value.strip().upper()


class DepartmentUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    code: str = Field(min_length=2, max_length=10)

    @field_validator("code")
    @classmethod
    def uppercase_code(cls, value: str) -> str:
        return value.strip().upper()


class AcademicYearCreate(BaseModel):
    academic_year: str = Field(pattern=r"^[0-9]{4}-[0-9]{2}$")


class SubjectCreate(BaseModel):
    subject_code: str = Field(min_length=2, max_length=20)
    subject_name: str = Field(min_length=3, max_length=180)
    semester_number: int = Field(ge=1, le=8)

    @field_validator("subject_code")
    @classmethod
    def uppercase_code(cls, value: str) -> str:
        return value.strip().upper()


class SubjectUpdate(SubjectCreate):
    pass


class OfferingCreate(BaseModel):
    academic_year: str = Field(pattern=r"^[0-9]{4}-[0-9]{2}$")
    semester_number: int = Field(ge=1, le=8)
    subject_code: str = Field(min_length=2, max_length=20)
    faculty_id: int = Field(gt=0)

    @field_validator("subject_code")
    @classmethod
    def uppercase_code(cls, value: str) -> str:
        return value.strip().upper()


class FeedbackPeriodUpsert(BaseModel):
    academic_year: str = Field(pattern=r"^[0-9]{4}-[0-9]{2}$")
    semester_number: int = Field(ge=1, le=8)
    start_date: datetime
    end_date: datetime

    @model_validator(mode="after")
    def end_after_start(self) -> "FeedbackPeriodUpsert":
        if self.end_date <= self.start_date:
            raise ValueError("End date must be after the start date.")
        return self


class FeedbackQuestionCreate(BaseModel):
    question_text: str = Field(min_length=5, max_length=500)
    is_active: bool = True


class FeedbackQuestionUpdate(BaseModel):
    question_text: str = Field(min_length=5, max_length=500)
    is_active: bool = True


class FacultyStatusUpdate(BaseModel):
    status: Literal["approved", "rejected", "inactive"]


class AdminStatusUpdate(BaseModel):
    is_active: bool


class AdminMemberCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: Email
    password: str
    confirm_password: str


class StudentAdminCreate(BaseModel):
    student_id: USN
    name: str = Field(min_length=2, max_length=120)
    department_id: int = Field(gt=0)
    password: str


class StudentAdminUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    department_id: int = Field(gt=0)


class FacultyAdminCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: Email
    department_id: int = Field(gt=0)
    password: str
    status: Literal["pending", "approved", "rejected", "inactive"] = "approved"
