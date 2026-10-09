"""authz: add home admin role

Revision ID: 0011
Revises: 0010
Create Date: 2026-10-10

`admin` — операционный администратор дома: управляет модулями/подмодулями
и участниками (edit), но, в отличие от `owner`, не назначает роли и не
удаляет дом (ролевые операции гейтятся по коду роли owner/superadmin).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """INSERT INTO authz.roles (code, name, scope, can_view, can_edit)
           SELECT 'admin', 'Admin', 'home', true, true
           WHERE NOT EXISTS (SELECT 1 FROM authz.roles WHERE code = 'admin')"""
    )


def downgrade() -> None:
    op.execute("DELETE FROM authz.roles WHERE code = 'admin'")