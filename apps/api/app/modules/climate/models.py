"""Модели модуля climate. Таблицы только в схеме climate."""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import JSON, TIMESTAMP, Float, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Device(Base):
    """Устройство климата; `id` совпадает с узлом-подмодулем tenancy."""

    __tablename__ = "devices"
    __table_args__ = {"schema": "climate"}

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True)
    module_node_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    kind: Mapped[str] = mapped_column(Text(), nullable=False)
    state: Mapped[dict] = mapped_column(JSON(), server_default=text("'{}'::jsonb"), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )


class Reading(Base):
    """Показание датчика (синтетическое)."""

    __tablename__ = "readings"
    __table_args__ = {"schema": "climate"}

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), primary_key=True, server_default=text("gen_random_uuid()")
    )
    device_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)
    metric: Mapped[str] = mapped_column(Text(), nullable=False)
    value: Mapped[float] = mapped_column(Float(), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )