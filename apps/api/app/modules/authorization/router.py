"""Админские эндпоинты authorization (только суперадмин)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import ApiError
from app.modules.authorization import service
from app.modules.authorization.models import Role, Superadmin
from app.modules.authorization.schemas import RoleRead, SuperadminRead
from app.modules.identity import service as identity_service
from app.modules.identity.models import User
from app.modules.identity.schemas import UserRead
from app.modules.tenancy import service as tenancy_service
from app.modules.tenancy.models import Resource
from app.modules.tenancy.schemas import ResourceRead

router = APIRouter(prefix="/admin", tags=["authorization"])


def _require_superadmin(db: Session, user: User) -> User:
    if not service.is_superadmin(db, user.id):
        raise ApiError("forbidden", "Требуются права суперадмина", status_code=403)
    return user


@router.get("/users", response_model=list[UserRead])
def admin_list_users(
    db: Session = Depends(get_db), user: User = Depends(identity_service.get_current_user)
) -> list[User]:
    _require_superadmin(db, user)
    return identity_service.list_users(db)


@router.get("/homes", response_model=list[ResourceRead])
def admin_list_homes(
    db: Session = Depends(get_db), user: User = Depends(identity_service.get_current_user)
) -> list[Resource]:
    _require_superadmin(db, user)
    return tenancy_service.list_home_nodes(db)


@router.get("/roles", response_model=list[RoleRead])
def admin_list_roles(
    db: Session = Depends(get_db), user: User = Depends(identity_service.get_current_user)
) -> list[Role]:
    _require_superadmin(db, user)
    return service.list_roles(db)


@router.get("/superadmins", response_model=list[SuperadminRead])
def admin_list_superadmins(
    db: Session = Depends(get_db), user: User = Depends(identity_service.get_current_user)
) -> list[Superadmin]:
    _require_superadmin(db, user)
    return service.list_superadmins(db)


@router.post(
    "/users/{user_id}/superadmin",
    response_model=SuperadminRead,
    status_code=status.HTTP_201_CREATED,
)
def admin_grant_superadmin(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(identity_service.get_current_user),
) -> Superadmin:
    _require_superadmin(db, user)
    identity_service.get_user(db, user_id)
    return service.grant_superadmin(db, user_id, user.id)


@router.delete("/users/{user_id}/superadmin", status_code=status.HTTP_204_NO_CONTENT)
def admin_revoke_superadmin(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(identity_service.get_current_user),
) -> None:
    _require_superadmin(db, user)
    service.revoke_superadmin(db, user_id)