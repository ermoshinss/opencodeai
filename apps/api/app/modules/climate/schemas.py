"""DTO модуля climate."""

from __future__ import annotations

import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field


class DeviceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    kind: str = Field(min_length=1, max_length=50)


class DeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    kind: str
    state: dict = Field(default_factory=dict)
    created_at: datetime.datetime


class ReadingRead(BaseModel):
    id: uuid.UUID
    metric: str
    value: float
    created_at: datetime.datetime


class CommandIn(BaseModel):
    command: str = Field(min_length=1, max_length=50)
    params: dict = Field(default_factory=dict)


class DeviceStatus(BaseModel):
    id: uuid.UUID
    name: str
    state: dict = Field(default_factory=dict)


class HomeStatusOut(BaseModel):
    enabled: bool
    device_count: int
    devices: list[DeviceStatus]