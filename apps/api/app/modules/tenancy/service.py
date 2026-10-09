"""Сервис tenancy: дерево «дом → модуль → подмодуль»."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.modules.registry import service as registry_service
from app.modules.tenancy.models import Resource

RESOURCE_TYPES = ("home", "module", "submodule")


def get_node(db: Session, node_id: uuid.UUID) -> Resource:
    node = db.get(Resource, node_id)
    if node is None:
        raise ApiError("resource_not_found", "Узел не найден", status_code=404)
    return node


def get_node_checked(db: Session, node_id: uuid.UUID, node_type: str) -> Resource:
    node = get_node(db, node_id)
    if node.node_type != node_type:
        raise ApiError(
            "invalid_node_type",
            f"Ожидался узел типа «{node_type}»",
            status_code=400,
        )
    return node


def ancestors(db: Session, node: Resource) -> list[Resource]:
    """Цепочка от узла до дома (включительно)."""
    chain: list[Resource] = []
    current: Resource | None = node
    while current is not None:
        chain.append(current)
        if current.parent_id is None:
            break
        current = db.get(Resource, current.parent_id)
    return chain


def get_home_node(db: Session, node: Resource) -> Resource:
    for item in ancestors(db, node):
        if item.node_type == "home":
            return item
    raise ApiError("corrupt_tree", "У дерева нет корневого дома", status_code=500)


def list_home_nodes(db: Session, home_ids: set[uuid.UUID] | None = None) -> list[Resource]:
    query = select(Resource).where(Resource.node_type == "home").order_by(Resource.name)
    if home_ids is not None:
        query = query.where(Resource.id.in_(home_ids))
    return list(db.scalars(query))


def create_home(db: Session, name: str) -> Resource:
    home = Resource(node_type="home", home_id=uuid.uuid4(), name=name)
    db.add(home)
    db.flush()
    home.home_id = home.id
    db.commit()
    db.refresh(home)
    return home


def enable_module(db: Session, home: Resource, module_code: str) -> Resource:
    catalog = registry_service.get_module_by_code(db, module_code)
    existing = db.scalar(
        select(Resource).where(
            Resource.home_id == home.id,
            Resource.module_code == module_code,
            Resource.node_type == "module",
        )
    )
    if existing is not None:
        return existing
    module = Resource(
        node_type="module",
        home_id=home.id,
        parent_id=home.id,
        module_code=module_code,
        name=catalog.title,
    )
    db.add(module)
    db.commit()
    db.refresh(module)
    return module


def list_module_nodes(db: Session, home: Resource) -> list[Resource]:
    return list(
        db.scalars(
            select(Resource)
            .where(Resource.home_id == home.id, Resource.node_type == "module")
            .order_by(Resource.name)
        )
    )


def get_module_node(db: Session, home: Resource, module_node_id: uuid.UUID) -> Resource:
    module = get_node_checked(db, module_node_id, "module")
    if module.home_id != home.id:
        raise ApiError("cross_home_access", "Модуль не принадлежит этому дому", status_code=400)
    return module


def create_submodule(db: Session, module: Resource, name: str) -> Resource:
    sub = Resource(
        node_type="submodule",
        home_id=module.home_id,
        parent_id=module.id,
        name=name,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def list_submodule_nodes(db: Session, module: Resource) -> list[Resource]:
    return list(
        db.scalars(
            select(Resource)
            .where(Resource.parent_id == module.id, Resource.node_type == "submodule")
            .order_by(Resource.name)
        )
    )


def ensure_node_in_home(db: Session, home_id: uuid.UUID, node_id: uuid.UUID) -> Resource:
    node = get_node(db, node_id)
    if node.home_id != home_id:
        raise ApiError("cross_home_access", "Узел не принадлежит этому дому", status_code=400)
    return node