"""Сервис authorization: роли, права, назначения, суперадмины.

Права решаются для узла ресурса (tenancy): «есть assignment пользователю с
ролью, чей scope покрывает узел или его предка». Наследование вниз по
дереву, edit ⇒ view, суперадмин — обход всего.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.modules.authorization.models import Role, RoleAssignment, Superadmin
from app.modules.tenancy import service as tenancy_service
from app.modules.tenancy.models import Resource

FORBIDDEN_ROLE_CODE = "superadmin"


def is_superadmin(db: Session, user_id: uuid.UUID) -> bool:
    return db.scalar(select(Superadmin).where(Superadmin.user_id == user_id)) is not None


def get_role(db: Session, role_code: str) -> Role:
    role = db.scalar(select(Role).where(Role.code == role_code))
    if role is None:
        raise ApiError("role_not_found", f"Роль '{role_code}' не найдена", status_code=404)
    return role


def list_roles(db: Session) -> list[Role]:
    return list(db.scalars(select(Role).order_by(Role.code)))


def effective_rights(db: Session, user_id: uuid.UUID, node_id: uuid.UUID) -> set[str]:
    """Права пользователя на узел: {view, edit} с учётом наследования."""
    if is_superadmin(db, user_id):
        return {"view", "edit"}

    node = tenancy_service.get_node(db, node_id)
    chain = tenancy_service.ancestors(db, node)
    chain_ids = {item.id for item in chain}

    rows = db.execute(
        select(RoleAssignment.scope_id, Role.can_view, Role.can_edit)
        .join(Role, Role.id == RoleAssignment.role_id)
        .where(RoleAssignment.user_id == user_id, RoleAssignment.scope_id.isnot(None))
    ).all()

    view, edit = False, False
    for scope_id, can_view, can_edit in rows:
        if scope_id not in chain_ids:
            continue
        view = view or bool(can_view)
        edit = edit or bool(can_edit)
    if edit:
        view = True
    rights: set[str] = set()
    if view:
        rights.add("view")
    if edit:
        rights.add("edit")
    return rights


def ensure_right(db: Session, user_id: uuid.UUID, node_id: uuid.UUID, right: str) -> None:
    tenancy_service.get_node(db, node_id)
    if right not in effective_rights(db, user_id, node_id):
        raise ApiError("forbidden", "Недостаточно прав", status_code=403)


def can_view_home(db: Session, user_id: uuid.UUID, home) -> bool:
    """Дом доступен, если есть view на него или любое назначение внутри."""
    if "view" in effective_rights(db, user_id, home.id):
        return True
    return home.id in eligible_home_ids(db, user_id)


def home_rights_for_me(db: Session, user_id: uuid.UUID, home) -> set[str]:
    """Права на дом для /auth/me (с учётом назначений на подузлы)."""
    rights = effective_rights(db, user_id, home.id)
    if not rights and home.id in eligible_home_ids(db, user_id):
        rights = {"view"}
    return rights


def is_owner(db: Session, user_id: uuid.UUID, node_id: uuid.UUID) -> bool:
    """Пользователь — owner дома (или суперадмин): управляет ролями."""
    if is_superadmin(db, user_id):
        return True
    node = tenancy_service.get_node(db, node_id)
    chain = tenancy_service.ancestors(db, node)
    chain_ids = {item.id for item in chain}
    owner_role = db.scalar(select(Role).where(Role.code == "owner"))
    if owner_role is None:
        return False
    assignment = db.scalar(
        select(RoleAssignment).where(
            RoleAssignment.user_id == user_id,
            RoleAssignment.role_id == owner_role.id,
            RoleAssignment.scope_id.in_(chain_ids),
        ).limit(1)
    )
    return assignment is not None


def ensure_owner(db: Session, user_id: uuid.UUID, node_id: uuid.UUID) -> None:
    if not is_owner(db, user_id, node_id):
        raise ApiError("forbidden", "Требуется владелец дома", status_code=403)


def eligible_home_ids(db: Session, user_id: uuid.UUID) -> set[uuid.UUID]:
    """Дома, где у пользователя есть назначение (в т.ч. на подузел)."""
    if is_superadmin(db, user_id):
        return set(db.scalars(select(Resource.id)).all())
    rows = db.execute(
        select(Resource.home_id)
        .join(RoleAssignment, RoleAssignment.scope_id == Resource.id)
        .where(RoleAssignment.user_id == user_id, RoleAssignment.scope_id.isnot(None))
    ).scalars().all()
    return {home_id for home_id in rows if home_id is not None}


def my_homes(db: Session, user_id: uuid.UUID) -> list[Resource]:
    ids = eligible_home_ids(db, user_id)
    return tenancy_service.list_home_nodes(db, ids)


def assign_role(
    db: Session,
    user_id: uuid.UUID,
    role_code: str,
    node_id: uuid.UUID,
) -> RoleAssignment:
    if role_code == FORBIDDEN_ROLE_CODE:
        raise ApiError(
            "role_not_assignable",
            "Роль superadmin назначается через суперадминов",
            status_code=400,
        )
    role = get_role(db, role_code)
    tenancy_service.get_node(db, node_id)
    existing = db.scalar(
        select(RoleAssignment).where(
            RoleAssignment.user_id == user_id,
            RoleAssignment.role_id == role.id,
            RoleAssignment.scope_id == node_id,
        )
    )
    if existing is not None:
        return existing
    assignment = RoleAssignment(user_id=user_id, role_id=role.id, scope_id=node_id)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def list_assignments(db: Session, home_id: uuid.UUID) -> list[RoleAssignment]:
    return list(
        db.scalars(
            select(RoleAssignment)
            .join(tenancy_service.Resource, tenancy_service.Resource.id == RoleAssignment.scope_id)
            .where(tenancy_service.Resource.home_id == home_id)
            .order_by(RoleAssignment.created_at)
        )
    )


def revoke_assignment(db: Session, assignment_id: uuid.UUID) -> None:
    assignment = db.get(RoleAssignment, assignment_id)
    if assignment is None:
        raise ApiError("assignment_not_found", "Назначение не найдено", status_code=404)
    db.delete(assignment)
    db.commit()


def list_superadmins(db: Session) -> list[Superadmin]:
    return list(db.scalars(select(Superadmin).order_by(Superadmin.created_at)))


def grant_superadmin(db: Session, user_id: uuid.UUID, actor: uuid.UUID) -> Superadmin:
    if is_superadmin(db, user_id):
        raise ApiError("already_superadmin", "Пользователь уже суперадмин", status_code=409)
    entry = Superadmin(user_id=user_id, granted_by=actor)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def revoke_superadmin(db: Session, user_id: uuid.UUID) -> None:
    entry = db.get(Superadmin, user_id)
    if entry is None:
        raise ApiError("not_superadmin", "Пользователь не суперадмин", status_code=404)
    db.delete(entry)
    db.commit()