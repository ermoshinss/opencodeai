"""Модели модуля registry. Таблицы только в схеме registry."""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import TIMESTAMP, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Module(Base):
    __tablename__ = "modules"
    __table_args__ = {"schema": "registry"}

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), primary_key=True, server_default=text("gen_random_uuid()")
    )
    code: Mapped[str] = mapped_column(Text(), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text(), nullable=False)
    version: Mapped[str] = mapped_column(Text(), nullable=False)
    state: Mapped[str] = mapped_column(Text(), server_default=text("'active'"), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )
