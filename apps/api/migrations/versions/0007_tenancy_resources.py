"""tenancy: resource tree (home → module → submodule)

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-10

Дерево ресурсов заменяет модель «workspace → project»:
- node_type home: parent NULL, name = дом;
- node_type module: parent = дом, module_code = каталог registry;
- node_type submodule: parent = модуль, данные живут в схеме модуля.

Таблицы `tenancy.workspaces|projects|workspace_members` ранней версии
остаются неиспользуемыми и будут удалены после перевода модулей.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "resources",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("home_id", sa.Uuid(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("node_type", sa.Text(), nullable=False),
        sa.Column("module_code", sa.Text(), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("config", sa.JSON(), server_default=sa.text("'{}'::jsonb"), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["tenancy.resources.id"],
            name="fk_resources_parent_id",
            ondelete="CASCADE",
        ),
        schema="tenancy",
    )
    op.create_index(
        "ux_resources_home_module",
        "resources",
        ["home_id", "module_code"],
        unique=True,
        postgresql_where=sa.text("node_type = 'module'"),
        schema="tenancy",
    )
    op.create_index("ix_resources_home_id", "resources", ["home_id"], schema="tenancy")
    op.create_index("ix_resources_parent_id", "resources", ["parent_id"], schema="tenancy")


def downgrade() -> None:
    op.drop_index("ix_resources_parent_id", table_name="resources", schema="tenancy")
    op.drop_index("ix_resources_home_id", table_name="resources", schema="tenancy")
    op.drop_index("ux_resources_home_module", table_name="resources", schema="tenancy")
    op.drop_table("resources", schema="tenancy")
