"""authorization schema

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-08

Имя схемы — `authz`: `authorization` — зарезервированное слово PostgreSQL
(нельзя создать как идентификатор без кавычек). Модуль остаётся `authorization`.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS authz")

    op.create_table(
        "permissions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("module_code", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("code", name="ux_permissions_code"),
        schema="authz",
    )

    op.create_table(
        "roles",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("code", name="ux_roles_code"),
        schema="authz",
    )

    op.create_table(
        "role_permissions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("permission_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["authz.roles.id"],
            name="fk_role_permissions_role_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["authz.permissions.id"],
            name="fk_role_permissions_permission_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("role_id", "permission_id", name="ux_role_permissions_role_perm"),
        schema="authz",
    )

    op.create_table(
        "role_assignments",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("scope_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["authz.roles.id"],
            name="fk_role_assignments_role_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("role_id", "user_id", "scope_id", name="ux_role_assignments_r_u_s"),
        schema="authz",
    )

    op.create_table(
        "superadmins",
        sa.Column("user_id", sa.Uuid(), primary_key=True),
        sa.Column("granted_by", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        schema="authz",
    )

    op.execute(
        """INSERT INTO authz.permissions (code, description, module_code)
           VALUES
             ('admin.read',     'Видеть все модули, workspace и grants', 'authorization'),
             ('admin.grant',    'Выдавать доступ к модулям',              'authorization'),
             ('mail.template.read', 'Читать шаблоны писем',              'mail'),
             ('mail.template.manage', 'Управлять шаблонами писем',       'mail'),
             ('mail.send',      'Отправлять письма',                      'mail'),
             ('mail.send.read', 'Читать историю отправок',               'mail')"""
    )

    op.execute(
        """INSERT INTO authz.roles (code, name, scope)
           VALUES
             ('superadmin', 'Superadmin', 'platform'),
             ('user',       'User',       'workspace'),
             ('admin',      'Admin',      'workspace')"""
    )


def downgrade() -> None:
    op.execute("DELETE FROM authz.roles WHERE code IN ('superadmin','user','admin')")
    op.execute("DELETE FROM authz.permissions WHERE code LIKE 'admin.%' OR module_code = 'mail'")
    op.drop_table("superadmins", schema="authz")
    op.drop_table("role_assignments", schema="authz")
    op.drop_table("role_permissions", schema="authz")
    op.drop_table("roles", schema="authz")
    op.drop_table("permissions", schema="authz")
    op.execute("DROP SCHEMA IF EXISTS authz")
