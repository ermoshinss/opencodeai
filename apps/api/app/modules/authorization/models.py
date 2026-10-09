"""Модели модуля authorization.

Схема authz (`authorization` — зарезервированное слово PostgreSQL) —
права, роли и суперадмины. Исключение: модель ModuleGrant отображает
`platform.module_grants` — разграничение доступа к модулям относится
к домену authorization, хотя таблица живёт в схеме ядра.
"""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import JSON, TIMESTAMP, Boolean, ForeignKey, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Permission(Base):
    __tablename__ = "permissions"
    __table_args__ = {"schema": "authz"}

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), primary_key=True, server_default=text("gen_random_uuid()")
    )
    code: Mapped[str] = mapped_column(Text(), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text(), nullable=False)
    module_code: Mapped[str] = mapped_column(Text(), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "authz"}

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), primary_key=True, server_default=text("gen_random_uuid()")
    )
    code: Mapped[str] = mapped_column(Text(), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    scope: Mapped[str] = mapped_column(Text(), nullable=False)
    can_view: Mapped[bool] = mapped_column(Boolean(), server_default=text("true"), nullable=False)
    can_edit: Mapped[bool] = mapped_column(Boolean(), server_default=text("false"), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = {"schema": "authz"}

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), primary_key=True, server_default=text("gen_random_uuid()")
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("authz.roles.id", ondelete="CASCADE"), nullable=False
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("authz.permissions.id", ondelete="CASCADE"), nullable=False
    )


class RoleAssignment(Base):
    __tablename__ = "role_assignments"
    __table_args__ = {"schema": "authz"}

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), primary_key=True, server_default=text("gen_random_uuid()")
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("authz.roles.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False)
    scope_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )


class Superadmin(Base):
    __tablename__ = "superadmins"
    __table_args__ = {"schema": "authz"}

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True)
    granted_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )


class ModuleGrant(Base):
    """Запись доступа workspace к модулю (схема platform, домен authorization)."""

    __tablename__ = "module_grants"
    __table_args__ = {"schema": "platform"}

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), primary_key=True, server_default=text("gen_random_uuid()")
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False)
    module_code: Mapped[str] = mapped_column(Text(), nullable=False)
    enabled: Mapped[bool] = mapped_column(nullable=False)
    config: Mapped[dict] = mapped_column(JSON(), server_default=text("'{}'::jsonb"), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )
