"""Health-check API."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.core.db import engine

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health() -> dict[str, str]:
    database = "ok"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        database = "error"
    return {"status": "ok", "database": database}
