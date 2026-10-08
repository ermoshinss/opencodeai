"""Alembic environment: одна БД, по схеме на модуль.

URL берётся из окружения/DATABASE_URL; приложение читает файл окружения
по переменной ENV_FILE (см. apps/api/app/core/config.py).
"""

from __future__ import annotations

import os
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine, pool
from sqlalchemy.engine import URL

CONFIG = context.config
MIGRATION_ROOT = Path(__file__).resolve().parent

target_metadata = None


def _database_url() -> str:
    env_file = os.getenv("ENV_FILE")
    if env_file and Path(env_file).exists():
        for line in Path(env_file).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("DATABASE_URL="):
                return line.removeprefix("DATABASE_URL=").strip()
    url = os.getenv("DATABASE_URL")
    if not url:
        url = "postgresql+psycopg://app_user:change-me@127.0.0.1:5433/opencodeai"
    return url


def run_migrations_offline() -> None:
    url = URL.create(_database_url())
    context.configure(url=url.render_as_string(hide_password=False), literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(_database_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
