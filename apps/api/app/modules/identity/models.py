"""Модели модуля identity. Таблицы только в схеме identity."""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import TIMESTAMP, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "identity"}

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), primary_key=True, server_default=text("gen_random_uuid()")
    )
    email: Mapped[str] = mapped_column(Text(), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )


class Session(Base):
    __tablename__ = "sessions"
    __table_args__ = {"schema": "identity"}

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(Text(), unique=True, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )
    expires_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime.datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
