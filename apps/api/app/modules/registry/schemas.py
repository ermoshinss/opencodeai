"""DTO модуля registry (часть OpenAPI-спеки)."""

from __future__ import annotations

import datetime
import uuid

from pydantic import BaseModel, ConfigDict


class ModuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    title: str
    version: str
    state: str


class ModuleFull(ModuleRead):
    id: uuid.UUID
    created_at: datetime.datetime
