"""Модели модуля tenancy. Таблицы только в схеме tenancy.

Ссылки на пользователей — по значению `user_id` без внешних ключей:
модули общаются через сервисы, целостность обеспечивает прикладной слой.
"""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import JSON, TIMESTAMP, ForeignKey, Index, Text, UniqueConstraint, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Resource(Base):
    """Узел дерева «Дом → Модуль → Подмодуль».

    node_type: home (parent NULL), module (parent = дом, module_code),
    submodule (parent = модуль). Данные подмодуля живут в схеме своего
    модуля и ссылаются на id узла.
    """

    __tablename__ = "resources"
    __table_args__ = (
        Index(
            "ux_resources_home_module",
            "home_id",
            "module_code",
            unique=True,
            postgresql_where=text("node_type = 'module'"),
        ),
        {"schema": "tenancy"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), primary_key=True, server_default=text("gen_random_uuid()")
    )
    home_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("tenancy.resources.id", ondelete="CASCADE"), nullable=True, index=True
    )
    node_type: Mapped[str] = mapped_column(Text(), nullable=False)
    module_code: Mapped[str | None] = mapped_column(Text(), nullable=True)
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    config: Mapped[dict] = mapped_column(JSON(), server_default=text("'{}'::jsonb"), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )


class Workspace(Base):
    __tablename__ = "workspaces"
    __table_args__ = {"schema": "tenancy"}

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), primary_key=True, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("workspace_id", "name", name="ux_projects_workspace_name"),
        {"schema": "tenancy"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), primary_key=True, server_default=text("gen_random_uuid()")
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("tenancy.workspaces.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="ux_workspace_members_ws_user"),
        {"schema": "tenancy"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), primary_key=True, server_default=text("gen_random_uuid()")
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("tenancy.workspaces.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False)
    role: Mapped[str] = mapped_column(Text(), nullable=False)
    joined_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )
