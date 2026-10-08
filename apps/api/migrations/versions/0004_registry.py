"""registry schema

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-08
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS registry")

    op.create_table(
        "modules",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), server_default=sa.text("'active'"), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("code", name="ux_modules_code"),
        schema="registry",
    )

    op.execute(
        """INSERT INTO registry.modules (code, title, version, state)
           VALUES ('mail', 'Mail', '0.1.0', 'active')"""
    )


def downgrade() -> None:
    op.execute("""DELETE FROM registry.modules WHERE code = 'mail'""")
    op.drop_table("modules", schema="registry")
    op.execute("DROP SCHEMA IF EXISTS registry")
