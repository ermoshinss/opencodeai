"""registry: smart home catalog

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-10

Каталог модулей умного дома. `mail` (веха 1) заменяется системами дома;
рабочая вертикаль — `climate`.
"""

from __future__ import annotations

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DELETE FROM registry.modules WHERE code = 'mail'")
    op.execute(
        """INSERT INTO registry.modules (code, title, version, state) VALUES
             ('climate',  'Климат',     '0.1.0', 'active'),
             ('security', 'Безопасность', '0.1.0', 'active'),
             ('energy',   'Энергия',    '0.1.0', 'active')
           ON CONFLICT (code) DO NOTHING"""
    )


def downgrade() -> None:
    op.execute("DELETE FROM registry.modules WHERE code IN ('climate', 'security', 'energy')")
    op.execute(
        """INSERT INTO registry.modules (code, title, version, state)
           VALUES ('mail', 'Mail', '0.1.0', 'active')
           ON CONFLICT (code) DO NOTHING"""
    )
