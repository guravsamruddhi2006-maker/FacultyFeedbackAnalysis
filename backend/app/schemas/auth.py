from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import Email, USN


class StudentRegister(BaseModel):
    student_id: USN
    name: str = Field(min_length=2, max_length=120)
    department_id: int = Field(gt=0)
    password: str
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self) -> "StudentRegister":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class FacultyRegister(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: Email
    department_id: int = Field(gt=0)
    password: str
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self) -> "FacultyRegister":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class AdminSetup(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: Email
    password: str
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self) -> "AdminSetup":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class AdminCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: Email
    password: str
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self) -> "AdminCreate":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class StudentLogin(BaseModel):
    student_id: USN
    password: str


class FacultyLogin(BaseModel):
    email: Email
    password: str


class AdminLogin(BaseModel):
    email: Email
    password: str


class ChangePassword(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self) -> "ChangePassword":
        if self.new_password != self.confirm_password:
            raise ValueError("New passwords do not match.")
        return self


class AuthUser(BaseModel):
    id: str
    role: str
    name: str
    email: str | None = None
    department_id: int | None = None
    status: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: str
    user: AuthUser
