"""DTO модуля authorization (часть OpenAPI-спеки)."""

from __future__ import annotations

import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field


class GrantUpsert(BaseModel):
    module_code: str = Field(min_length=1, max_length=100)
    enabled: bool = True


class GrantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    workspace_id: uuid.UUID
    module_code: str
    enabled: bool
    config: dict
    updated_at: datetime.datetime


class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    scope: str


class SuperadminRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    granted_by: uuid.UUID | None
    created_at: datetime.datetime
