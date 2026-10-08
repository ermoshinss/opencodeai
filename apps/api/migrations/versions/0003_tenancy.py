"""tenancy schema

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-08
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS tenancy")

    op.create_table(
        "workspaces",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
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
        schema="tenancy",
    )

    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
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
            ["workspace_id"],
            ["tenancy.workspaces.id"],
            name="fk_projects_workspace_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("workspace_id", "name", name="ux_projects_workspace_name"),
        schema="tenancy",
    )
    op.create_index(
        "ix_projects_workspace_id",
        "projects",
        ["workspace_id"],
        schema="tenancy",
    )

    op.create_table(
        "workspace_members",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column(
            "joined_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["tenancy.workspaces.id"],
            name="fk_workspace_members_workspace_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("workspace_id", "user_id", name="ux_workspace_members_ws_user"),
        schema="tenancy",
    )
    op.create_index(
        "ix_workspace_members_user_id",
        "workspace_members",
        ["user_id"],
        schema="tenancy",
    )


def downgrade() -> None:
    op.drop_index("ix_workspace_members_user_id", table_name="workspace_members", schema="tenancy")
    op.drop_table("workspace_members", schema="tenancy")
    op.drop_index("ix_projects_workspace_id", table_name="projects", schema="tenancy")
    op.drop_table("projects", schema="tenancy")
    op.drop_table("workspaces", schema="tenancy")
    op.execute("DROP SCHEMA IF EXISTS tenancy")
