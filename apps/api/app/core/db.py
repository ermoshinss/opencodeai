"""Подключение к PostgreSQL.

Одна БД, отдельная схема на модуль. Таблицы всегда указываются
явным схемным именем (например `tenancy.workspaces`), `search_path`
не используется.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """База для моделей модулей. Метаданные моделей не используются
    миграциями: схема описывается только ревизиями Alembic."""


def get_db() -> Generator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
