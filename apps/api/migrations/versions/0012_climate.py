"""climate: schema, devices, readings

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-10

Модуль БД вертикали «климат»: устройства-подмодули (id = узел tenancy)
и синтетические показания.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS climate")
    op.create_table(
        "devices",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("module_node_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("state", sa.JSON(), server_default=sa.text("'{}'::jsonb"), nullable=False),
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
        schema="climate",
    )
    op.create_index(
        "ix_climate_devices_module_node", "devices", ["module_node_id"], schema="climate"
    )
    op.create_table(
        "readings",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("device_id", sa.Uuid(), nullable=False),
        sa.Column("metric", sa.Text(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        schema="climate",
    )
    op.create_index(
        "ix_climate_readings_device", "readings", ["device_id"], schema="climate"
    )


def downgrade() -> None:
    op.drop_index("ix_climate_readings_device", table_name="readings", schema="climate")
    op.drop_table("readings", schema="climate")
    op.drop_index("ix_climate_devices_module_node", table_name="devices", schema="climate")
    op.drop_table("devices", schema="climate")
    op.execute("DROP SCHEMA IF EXISTS climate")