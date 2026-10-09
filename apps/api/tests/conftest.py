"""Тестовая БД: создание, миграции, очистка.

Используется отдельная БД `opencodeai_test` (app_user имеет CREATEDB).
Пароль берётся из окружения или секретного файла
`~/.config/opencodeai/.env`.
"""

from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path

import psycopg
import pytest

ROOT = Path(__file__).resolve().parents[3]
TEST_DB = "opencodeai_test"
HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
PORT = int(os.getenv("POSTGRES_PORT", "5433"))
USER = os.getenv("POSTGRES_USER", "app_user")

SUPERADMIN_EMAIL = "ermoshinss"
SUPERADMIN_PASSWORD = "synthetic-superadmin-pass"


def _password() -> str:
    password = os.getenv("POSTGRES_PASSWORD")
    if password:
        return password
    secure = Path.home() / ".config/opencodeai/.env"
    if secure.exists():
        for line in secure.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("POSTGRES_PASSWORD="):
                return line.removeprefix("POSTGRES_PASSWORD=").strip()
    raise RuntimeError("POSTGRES_PASSWORD не задан и не найден в ~/.config/opencodeai/.env")


_password_value = _password()

_env_file = Path("/tmp") / f"opencodeai-test-{uuid.uuid4().hex[:8]}.env"
_env_file.write_text(
    "\n".join(
        [
            f"POSTGRES_HOST={HOST}",
            f"POSTGRES_PORT={PORT}",
            f"POSTGRES_DB={TEST_DB}",
            f"POSTGRES_USER={USER}",
            f"POSTGRES_PASSWORD={_password_value}",
            f"DATABASE_URL=postgresql+psycopg://{USER}:{_password_value}@{HOST}:{PORT}/{TEST_DB}",
            f"SUPERADMIN_EMAIL={SUPERADMIN_EMAIL}",
            f"SUPERADMIN_PASSWORD={SUPERADMIN_PASSWORD}",
            "",
        ]
    ),
    encoding="utf-8",
)
os.environ["ENV_FILE"] = str(_env_file)


def _connect_admin():
    return psycopg.connect(
        dbname="postgres",
        user=USER,
        password=_password_value,
        host=HOST,
        port=PORT,
        autocommit=True,
    )


def _recreate_database() -> None:
    with _connect_admin() as conn:
        with conn.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS {TEST_DB} WITH (FORCE)")
            cur.execute(f"CREATE DATABASE {TEST_DB} OWNER {USER}")


def _run_migrations() -> None:
    alembic_ini = ROOT / "apps/api/alembic.ini"
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(alembic_ini), "upgrade", "head"],
        cwd=ROOT,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"alembic upgrade failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


_recreate_database()
_run_migrations()


@pytest.fixture(scope="session", autouse=True)
def _test_database() -> None:
    yield
    _env_file.unlink(missing_ok=True)
    with _connect_admin() as conn:
        with conn.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS {TEST_DB} WITH (FORCE)")
