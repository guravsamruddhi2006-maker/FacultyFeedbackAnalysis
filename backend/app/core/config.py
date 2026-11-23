from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent
for candidate in (PROJECT_DIR / ".env", BACKEND_DIR / ".env"):
    if candidate.exists():
        load_dotenv(candidate, override=False)


def _csv_env(name: str, default: str) -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = "FacultyInsight AI"
    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    api_prefix: str = "/api"
    jwt_secret_key: str = field(default_factory=lambda: os.getenv("JWT_SECRET_KEY", ""))
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = field(default_factory=lambda: int(os.getenv("ACCESS_TOKEN_MINUTES", "30")))
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", ""))
    db_host: str = field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    db_port: int = field(default_factory=lambda: int(os.getenv("DB_PORT", "5432")))
    db_name: str = field(default_factory=lambda: os.getenv("DB_NAME", "faculty_feedback"))
    db_user: str = field(default_factory=lambda: os.getenv("DB_USER", "postgres"))
    db_password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", ""))
    cors_origins: list[str] = field(
        default_factory=lambda: _csv_env(
            "CORS_ORIGINS",
            "http://localhost:5173,http://localhost:4173,http://localhost:3000,http://localhost:8080",
        )
    )
    login_rate_limit: int = field(default_factory=lambda: int(os.getenv("LOGIN_RATE_LIMIT", "12")))
    login_rate_window_seconds: int = field(
        default_factory=lambda: int(os.getenv("LOGIN_RATE_WINDOW_SECONDS", "300"))
    )
    db_connect_timeout: int = field(default_factory=lambda: int(os.getenv("DB_CONNECT_TIMEOUT", "10")))
    db_connect_retries: int = field(default_factory=lambda: int(os.getenv("DB_CONNECT_RETRIES", "2")))
    max_page_size: int = 100

    def validate(self) -> None:
        if not self.jwt_secret_key or len(self.jwt_secret_key) < 16:
            raise RuntimeError(
                "JWT_SECRET_KEY must be set to a random value of at least 16 characters."
            )
        if self.app_env == "production" and "change-me" in self.jwt_secret_key.lower():
            raise RuntimeError("Refusing to start production with the example JWT secret.")

    @property
    def db_conninfo(self) -> dict[str, object]:
        if self.database_url:
            return {"conninfo": self.database_url}
        return {
            "host": self.db_host,
            "port": self.db_port,
            "dbname": self.db_name,
            "user": self.db_user,
            "password": self.db_password,
        }


settings = Settings()
