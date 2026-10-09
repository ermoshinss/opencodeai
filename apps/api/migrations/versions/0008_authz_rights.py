"""authz: role as rights template, assignment to resource node

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-10

Права узла — `view` (can_view) и `edit` (can_edit, подразумевает view).
Роль = шаблон прав; назначение (role_id, user_id, scope_id) ссылается на
узел дерева `tenancy.resources` (дом/модуль/подмодуль). Права наследуются
вниз по дереву, эффективные права = максимум по покрывающим назначениям.

Справочники `authz.permissions|role_permissions` ранней версии не участвуют
в проверке (права узла задаются can_view/can_edit) — остаются неиспользуемыми.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "roles",
        sa.Column("can_view", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        schema="authz",
    )
    op.add_column(
        "roles",
        sa.Column("can_edit", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        schema="authz",
    )

    op.execute("DELETE FROM authz.roles WHERE code = 'admin'")

    op.execute(
        """INSERT INTO authz.roles (code, name, scope, can_view, can_edit)
           SELECT 'owner', 'Owner', 'home', true, true
           WHERE NOT EXISTS (SELECT 1 FROM authz.roles WHERE code = 'owner')"""
    )

    op.execute(
        """UPDATE authz.roles SET scope = 'platform', can_view = true, can_edit = true
           WHERE code = 'superadmin'"""
    )
    op.execute(
        """UPDATE authz.roles SET scope = 'home', name = 'Owner', can_view = true, can_edit = true
           WHERE code = 'owner'"""
    )
    op.execute(
        """UPDATE authz.roles SET scope = 'resource', can_view = true, can_edit = false
           WHERE code = 'user'"""
    )


def downgrade() -> None:
    op.execute("DELETE FROM authz.roles WHERE code = 'owner'")
    op.execute(
        """INSERT INTO authz.roles (code, name, scope)
           SELECT 'admin', 'Admin', 'workspace'
           WHERE NOT EXISTS (SELECT 1 FROM authz.roles WHERE code = 'admin')"""
    )
    op.execute("""UPDATE authz.roles SET scope = 'workspace' WHERE code IN ('user', 'admin')""")
    op.execute(
        """UPDATE authz.roles SET scope = 'platform', can_edit = false WHERE code = 'superadmin'"""
    )
    op.drop_column("roles", "can_edit", schema="authz")
    op.drop_column("roles", "can_view", schema="authz")
