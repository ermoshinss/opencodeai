"""Сервис модуля authorization: права, суперадмины, доступ к модулям.

Внутри модуля используются только таблицы своей схемы и платформенная
`platform.module_grants` (разграничение доступа — домен authorization).
Данные других модулей — через их сервисы, не SQL по чужим схемам.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.authorization.models import ModuleGrant, Role, Superadmin
from app.modules.registry import service as registry_service
from app.modules.tenancy import service as tenancy_service


def is_superadmin(db: Session, user_id: uuid.UUID) -> bool:
    return db.get(Superadmin, user_id) is not None


def list_superadmins(db: Session) -> list[Superadmin]:
    return list(db.scalars(select(Superadmin).order_by(Superadmin.created_at)))


def list_roles(db: Session) -> list[Role]:
    return list(db.scalars(select(Role).order_by(Role.code)))


def list_grants(db: Session) -> list[ModuleGrant]:
    return list(db.scalars(select(ModuleGrant).order_by(ModuleGrant.created_at)))


def upsert_grant(
    db: Session, workspace_id: uuid.UUID, module_code: str, enabled: bool
) -> ModuleGrant:
    registry_service.get_module_by_code(db, module_code)
    tenancy_service.get_workspace(db, workspace_id)
    grant = db.scalar(
        select(ModuleGrant).where(
            ModuleGrant.workspace_id == workspace_id,
            ModuleGrant.module_code == module_code,
        )
    )
    if grant is None:
        grant = ModuleGrant(
            workspace_id=workspace_id,
            module_code=module_code,
            enabled=enabled,
            config={},
        )
        db.add(grant)
    else:
        grant.enabled = enabled
    db.commit()
    db.refresh(grant)
    return grant
