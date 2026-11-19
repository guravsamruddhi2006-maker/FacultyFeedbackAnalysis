from __future__ import annotations

from pydantic import BaseModel, Field


class RatingInput(BaseModel):
    question_id: int = Field(gt=0)
    rating: int = Field(ge=1, le=5, description="1=Very Poor, 5=Excellent")


class FeedbackSubmit(BaseModel):
    # student_id is intentionally absent: it is always derived from the JWT.
    offering_id: int = Field(gt=0)
    ratings: list[RatingInput] = Field(min_length=1)
    comment: str = Field(min_length=10, max_length=1000)


class FeedbackUpdate(BaseModel):
    ratings: list[RatingInput] = Field(min_length=1)
    comment: str = Field(min_length=10, max_length=1000)


class FeedbackAnswerOut(BaseModel):
    question_id: int
    question_text: str
    rating: int


class FeedbackOut(BaseModel):
    feedback_id: int
    offering_id: int
    submitted_at: str
    updated_at: str | None
    comment: str
    answers: list[FeedbackAnswerOut]
    editable: bool
