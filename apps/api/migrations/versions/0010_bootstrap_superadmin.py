"""bootstrap superadmin account

Revision ID: 0010
Revises: 0009
Create Date: 2026-10-10

Создаёт суперадмина платформы. Учётные данные берутся из окружения:
- SUPERADMIN_EMAIL    (по умолчанию `ermoshinss`);
- SUPERADMIN_PASSWORD (не хранится в репозитории).

`granted_by = NULL` — единственный bootstrap-бэкдор: дальнейшие суперадмины
назначаются только действующими суперадминами (админ-API) или SQL.
Если пароль не задан (CI/безопасное окружение), роль не создаётся.
"""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path

import sqlalchemy as sa
from alembic import op

log = logging.getLogger("alembic.runtime.migration")

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None

PBKDF2_ITERATIONS = 260_000


def _from_envfile(key: str) -> str:
    env_file = os.getenv("ENV_FILE")
    if env_file and Path(env_file).exists():
        for line in Path(env_file).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(f"{key}="):
                return line.removeprefix(f"{key}=").strip()
    return ""


SUPERADMIN_EMAIL = (
    os.getenv("SUPERADMIN_EMAIL") or _from_envfile("SUPERADMIN_EMAIL") or "ermoshinss"
)
SUPERADMIN_PASSWORD = os.getenv("SUPERADMIN_PASSWORD") or _from_envfile("SUPERADMIN_PASSWORD")

PBKDF2_ITERATIONS = 260_000


def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def upgrade() -> None:
    if not SUPERADMIN_PASSWORD:
        log.warning(
            "SUPERADMIN_PASSWORD не задан в окружении — суперадмин не создан (migration 0010)"
        )
        return

    conn = op.get_bind()
    user_id = conn.execute(
        sa.text("SELECT id FROM identity.users WHERE email = :email"),
        {"email": SUPERADMIN_EMAIL},
    ).scalar()

    if user_id is None:
        user_id = conn.execute(
            sa.text(
                "INSERT INTO identity.users (email, name, password_hash) "
                "VALUES (:email, :name, :hash) RETURNING id"
            ),
            {
                "email": SUPERADMIN_EMAIL,
                "name": SUPERADMIN_EMAIL,
                "hash": _hash_password(SUPERADMIN_PASSWORD),
            },
        ).scalar()
    else:
        conn.execute(
            sa.text("UPDATE identity.users SET password_hash = :hash WHERE id = :id"),
            {"hash": _hash_password(SUPERADMIN_PASSWORD), "id": user_id},
        )

    conn.execute(
        sa.text(
            "INSERT INTO authz.superadmins (user_id, granted_by) VALUES (:user_id, NULL) "
            "ON CONFLICT (user_id) DO NOTHING"
        ),
        {"user_id": user_id},
    )


def downgrade() -> None:
    conn = op.get_bind()
    user_id = conn.execute(
        sa.text("SELECT id FROM identity.users WHERE email = :email"),
        {"email": SUPERADMIN_EMAIL},
    ).scalar()
    if user_id is None:
        return
    conn.execute(
        sa.text("DELETE FROM authz.superadmins WHERE user_id = :user_id AND granted_by IS NULL"),
        {"user_id": user_id},
    )
    conn.execute(
        sa.text("DELETE FROM identity.sessions WHERE user_id = :user_id"),
        {"user_id": user_id},
    )
    conn.execute(
        sa.text("DELETE FROM identity.users WHERE id = :user_id"),
        {"user_id": user_id},
    )
