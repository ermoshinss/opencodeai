"""identity: credentials and sessions

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-10

Пароль пользователя + сессии (см. core/security). Токен сессии в БД
хранится хэшем (sha256); формат пароля `pbkdf2_sha256$iterations$salt$hash`.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("password_hash", sa.Text(), nullable=True),
        schema="identity",
    )

    op.create_table(
        "sessions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.UniqueConstraint("token_hash", name="ux_sessions_token_hash"),
        schema="identity",
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"], schema="identity")


def downgrade() -> None:
    op.drop_index("ix_sessions_user_id", table_name="sessions", schema="identity")
    op.drop_table("sessions", schema="identity")
    op.drop_column("users", "password_hash", schema="identity")
