"""DTO модуля authorization (роли, назначения, суперадмины)."""

from __future__ import annotations

import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field


class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    scope: str
    can_view: bool
    can_edit: bool


class SuperadminRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    granted_by: uuid.UUID | None
    created_at: datetime.datetime


class AssignmentCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    role_code: str = Field(min_length=1, max_length=50)
    node_id: uuid.UUID | None = None


class AssignmentRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    email: str
    role_code: str
    role_name: str
    node_id: uuid.UUID
    node_name: str
    created_at: datetime.datetime