"""Unit tests for the login rate limiter dependency."""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.core.deps import LoginRateLimiter


def _request(path: str = "/api/auth/student/login", ip: str = "203.0.113.10") -> SimpleNamespace:
    return SimpleNamespace(
        url=SimpleNamespace(path=path),
        headers={"x-forwarded-for": ip},
        client=SimpleNamespace(host=ip),
    )


def test_login_rate_limiter_allows_up_to_configured_limit() -> None:
    limiter = LoginRateLimiter()
    for _ in range(settings.login_rate_limit):
        limiter(_request())
    # The next attempt inside the window must be rejected with 429.
    with pytest.raises(HTTPException) as exc_info:
        limiter(_request())
    assert exc_info.value.status_code == 429
    assert exc_info.value.headers.get("Retry-After")


def test_login_rate_limiter_reset_clears_the_bucket() -> None:
    limiter = LoginRateLimiter()
    for _ in range(settings.login_rate_limit):
        limiter(_request())
    limiter.reset(_request())
    limiter(_request())
    limiter(_request())


def test_login_rate_limiter_keys_by_ip_and_path() -> None:
    limiter = LoginRateLimiter()
    for _ in range(settings.login_rate_limit):
        limiter(_request(path="/api/auth/student/login"))
    # A different path has an independent bucket.
    limiter(_request(path="/api/auth/faculty/login"))
