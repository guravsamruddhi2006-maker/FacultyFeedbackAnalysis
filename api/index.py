"""Vercel serverless entry for the FacultyInsight AI FastAPI application.

Exposes the existing FastAPI ASGI application (`app.main:app`) as a Vercel
Python serverless function at /api. No application code is changed; the existing
architecture is preserved.
"""

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_BACKEND_DIR = _PROJECT_ROOT / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.main import app  # noqa: E402,F401,F403

__all__ = ["app"]
