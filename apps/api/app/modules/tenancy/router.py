"""Эндпоинты дерева ресурсов: дом → модуль → подмодуль, назначение ролей."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import ApiError
from app.modules.authorization import service as authz_service
from app.modules.authorization.models import Role, RoleAssignment
from app.modules.authorization.schemas import AssignmentCreate, AssignmentRead
from app.modules.identity import service as identity_service
from app.modules.identity.models import User
from app.modules.tenancy import service
from app.modules.tenancy.models import Resource
from app.modules.tenancy.schemas import (
    HomeCreate,
    ModuleEnableIn,
    ResourceRead,
    SubmoduleCreate,
)

router = APIRouter(prefix="/homes", tags=["tenancy"])


@router.post("", response_model=ResourceRead, status_code=status.HTTP_201_CREATED)
def create_home(
    data: HomeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(identity_service.get_current_user),
) -> Resource:
    home = service.create_home(db, data.name)
    authz_service.assign_role(db, user.id, "owner", home.id)
    return home


@router.get("", response_model=list[ResourceRead])
def list_homes(
    db: Session = Depends(get_db),
    user: User = Depends(identity_service.get_current_user),
) -> list[Resource]:
    return authz_service.my_homes(db, user.id)


@router.get("/{home_id}", response_model=ResourceRead)
def get_home(
    home_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(identity_service.get_current_user),
) -> Resource:
    home = service.get_node_checked(db, home_id, "home")
    if not authz_service.can_view_home(db, user.id, home):
        raise ApiError("forbidden", "Недостаточно прав", status_code=403)
    return home


@router.get("/{home_id}/modules", response_model=list[ResourceRead])
def list_modules(
    home_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(identity_service.get_current_user),
) -> list[Resource]:
    home = service.get_node_checked(db, home_id, "home")
    if not authz_service.can_view_home(db, user.id, home):
        raise ApiError("forbidden", "Недостаточно прав", status_code=403)
    return service.list_module_nodes(db, home)


@router.post("/{home_id}/modules", response_model=ResourceRead, status_code=status.HTTP_201_CREATED)
def enable_module(
    home_id: uuid.UUID,
    data: ModuleEnableIn,
    db: Session = Depends(get_db),
    user: User = Depends(identity_service.get_current_user),
) -> Resource:
    home = service.get_node_checked(db, home_id, "home")
    authz_service.ensure_right(db, user.id, home.id, "edit")
    return service.enable_module(db, home, data.module_code)


@router.get("/{home_id}/modules/{module_id}/submodules", response_model=list[ResourceRead])
def list_submodules(
    home_id: uuid.UUID,
    module_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(identity_service.get_current_user),
) -> list[Resource]:
    home = service.get_node_checked(db, home_id, "home")
    module = service.get_module_node(db, home, module_id)
    authz_service.ensure_right(db, user.id, module.id, "view")
    return service.list_submodule_nodes(db, module)


@router.post(
    "/{home_id}/modules/{module_id}/submodules",
    response_model=ResourceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_submodule(
    home_id: uuid.UUID,
    module_id: uuid.UUID,
    data: SubmoduleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(identity_service.get_current_user),
) -> Resource:
    home = service.get_node_checked(db, home_id, "home")
    module = service.get_module_node(db, home, module_id)
    authz_service.ensure_right(db, user.id, module.id, "edit")
    return service.create_submodule(db, module, data.name)


@router.get("/{home_id}/roles", response_model=list[AssignmentRead])
def list_role_assignments(
    home_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(identity_service.get_current_user),
) -> list[AssignmentRead]:
    home = service.get_node_checked(db, home_id, "home")
    authz_service.ensure_owner(db, user.id, home.id)
    return [_build_assignment(db, item) for item in authz_service.list_assignments(db, home.id)]


@router.post("/{home_id}/roles", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED)
def assign_home_role(
    home_id: uuid.UUID,
    data: AssignmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(identity_service.get_current_user),
) -> AssignmentRead:
    home = service.get_node_checked(db, home_id, "home")
    authz_service.ensure_owner(db, user.id, home.id)
    target = identity_service.get_user_by_email(db, data.email)
    if target is None:
        raise ApiError("user_not_found", "Пользователь с таким email не найден", status_code=404)
    node = service.ensure_node_in_home(db, home.id, data.node_id or home.id)
    assignment = authz_service.assign_role(db, target.id, data.role_code, node.id)
    return _build_assignment(db, assignment)


@router.delete("/{home_id}/roles/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_home_role(
    home_id: uuid.UUID,
    assignment_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(identity_service.get_current_user),
) -> None:
    home = service.get_node_checked(db, home_id, "home")
    authz_service.ensure_owner(db, user.id, home.id)
    assignment = db.get(RoleAssignment, assignment_id)
    if assignment is None:
        raise ApiError("assignment_not_found", "Назначение не найдено", status_code=404)
    if assignment.scope_id is None:
        raise ApiError("bad_assignment", "Назначение без узла", status_code=400)
    service.ensure_node_in_home(db, home.id, assignment.scope_id)
    authz_service.revoke_assignment(db, assignment.id)


def _build_assignment(db: Session, assignment: RoleAssignment) -> AssignmentRead:
    if assignment.scope_id is None:
        raise ApiError("bad_assignment", "Назначение без узла", status_code=400)
    role = db.get(Role, assignment.role_id)
    node = service.get_node(db, assignment.scope_id)
    user_rec = identity_service.get_user(db, assignment.user_id)
    return AssignmentRead(
        id=assignment.id,
        user_id=assignment.user_id,
        email=user_rec.email,
        role_code=role.code if role is not None else "?",
        role_name=role.name if role is not None else "?",
        node_id=node.id,
        node_name=node.name,
        created_at=assignment.created_at,
    )