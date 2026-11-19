from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.analytics.service import faculty_dashboard
from app.analytics.text import predict_sentiment, sentiment_engine_info
from app.core.deps import Principal, authenticated, faculty_required
from app.db import get_db


router = APIRouter(prefix="/ml", tags=["AI / NLP"])


class TextItem(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


class AnalyzeRequest(BaseModel):
    texts: list[TextItem] = Field(min_length=1, max_length=50)


@router.get("/model-info")
def model_info(_: Principal = Depends(authenticated)):
    return {
        **sentiment_engine_info(),
        "training_script": "ml/train.py",
        "labels": ["positive", "neutral", "negative"],
        "note": "The default engine is an explainable lexicon baseline. A trained model is used only when validated metadata is present.",
    }


@router.post("/sentiment")
def analyze_texts(payload: AnalyzeRequest, _: Principal = Depends(authenticated)):
    return {
        "method": sentiment_engine_info()["active_engine"],
        "results": [{"text": item.text, **predict_sentiment(item.text)} for item in payload.texts],
    }


@router.get("/insights")
def insights_for_current_faculty(
    academic_year: str | None = None,
    semester_number: int | None = Query(default=None, ge=1, le=8),
    subject_code: str | None = None,
    current_user: Principal = Depends(faculty_required),
    conn=Depends(get_db),
) -> dict[str, Any]:
    data = faculty_dashboard(
        conn,
        int(current_user.id),
        academic_year=academic_year,
        semester_number=semester_number,
        subject_code=subject_code,
    )
    insights = data.get("insights") or {}
    return {
        "faculty_id": data.get("faculty_id"),
        "generated_at": insights.get("generated_at"),
        "overall_average_rating": insights.get("overall_average_rating"),
        "response_count": insights.get("response_count"),
        "strengths": insights.get("strengths") or [],
        "improvement_areas": insights.get("improvement_areas") or [],
        "recommendations": insights.get("recommendations") or [],
        "trend_insights": data.get("trend_insights") or [],
        "sentiment": insights.get("sentiment") or {},
        "methodology": insights.get("methodology") or {},
    }
