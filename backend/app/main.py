from __future__ import annotations

import logging
import time
from uuid import uuid4

import psycopg
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app import __version__
from app.api import admin, analytics, auth, catalog, faculty, ml, reports, students
from app.core.config import settings
from app.db import connect


logger = logging.getLogger("facultyinsight")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
settings.validate()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid4()))
        started = time.perf_counter()
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cache-Control"] = response.headers.get("Cache-Control", "no-store")
        if settings.app_env == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        duration = (time.perf_counter() - started) * 1000
        logger.info("%s %s %s %.1fms req=%s", request.method, request.url.path, response.status_code, duration, request_id)
        return response


app = FastAPI(
    title=settings.app_name,
    description=(
        "Intelligent faculty feedback analysis for a CSE department. "
        "Anonymous student feedback, strict faculty-level isolation, analytics and explainable NLP."
    ),
    version=__version__,
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url="/redoc" if settings.app_env != "production" else None,
    openapi_url="/openapi.json" if settings.app_env != "production" else None,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["Content-Disposition", "X-Request-ID"],
)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Please check the submitted values.",
            "errors": [
                {"field": ".".join(str(part) for part in error.get("loc", [])[1:]), "message": error.get("msg")}
                for error in exc.errors()
            ],
        },
    )


@app.exception_handler(psycopg.OperationalError)
async def database_unavailable_handler(request: Request, exc: psycopg.OperationalError):
    logger.exception("Database unavailable")
    return JSONResponse(status_code=503, content={"detail": "The database is temporarily unavailable."})


@app.exception_handler(Exception)
async def safe_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred. Please try again."})


@app.get("/", tags=["Health"])
def root():
    return {
        "name": settings.app_name,
        "tagline": "Turning Student Feedback into Better Teaching.",
        "version": __version__,
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "facultyinsight-api", "version": __version__}


@app.get("/health/db", tags=["Health"])
def health_db():
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 AS ok")
            cur.fetchone()
    finally:
        conn.close()
    return {"status": "ok", "database": "connected"}


for router in (
    auth.router,
    catalog.router,
    admin.router,
    faculty.router,
    students.router,
    analytics.router,
    ml.router,
    reports.router,
):
    app.include_router(router, prefix=settings.api_prefix)
