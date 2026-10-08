"""Админские эндпоинты модуля authorization.

Заглушка прав: схема прав создана, но проверка ролей не выполняется
(включается вместе с RBAC после сквозного сценария). Обзор других модулей —
через их сервисы.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.authorization import service
from app.modules.authorization.models import ModuleGrant, Role, Superadmin
from app.modules.authorization.schemas import GrantRead, GrantUpsert, RoleRead, SuperadminRead
from app.modules.identity import service as identity_service
from app.modules.identity.models import User
from app.modules.identity.schemas import UserRead
from app.modules.registry import service as registry_service
from app.modules.registry.models import Module
from app.modules.registry.schemas import ModuleRead
from app.modules.tenancy import service as tenancy_service
from app.modules.tenancy.models import Workspace
from app.modules.tenancy.schemas import WorkspaceRead

router = APIRouter(prefix="/admin", tags=["authorization"])


@router.get("/users", response_model=list[UserRead])
def admin_list_users(db: Session = Depends(get_db)) -> list[User]:
    return identity_service.list_users(db)


@router.get("/workspaces", response_model=list[WorkspaceRead])
def admin_list_workspaces(db: Session = Depends(get_db)) -> list[Workspace]:
    return tenancy_service.list_workspaces(db)


@router.get("/modules", response_model=list[ModuleRead])
def admin_list_modules(db: Session = Depends(get_db)) -> list[Module]:
    return registry_service.list_modules(db)


@router.get("/superadmins", response_model=list[SuperadminRead])
def admin_list_superadmins(db: Session = Depends(get_db)) -> list[Superadmin]:
    return service.list_superadmins(db)


@router.get("/roles", response_model=list[RoleRead])
def admin_list_roles(db: Session = Depends(get_db)) -> list[Role]:
    return service.list_roles(db)


@router.get("/grants", response_model=list[GrantRead])
def admin_list_grants(db: Session = Depends(get_db)) -> list[ModuleGrant]:
    return service.list_grants(db)


@router.post(
    "/workspaces/{workspace_id}/modules",
    response_model=GrantRead,
    status_code=status.HTTP_201_CREATED,
)
def admin_upsert_grant(
    workspace_id: uuid.UUID, data: GrantUpsert, db: Session = Depends(get_db)
) -> ModuleGrant:
    return service.upsert_grant(db, workspace_id, data.module_code, data.enabled)
