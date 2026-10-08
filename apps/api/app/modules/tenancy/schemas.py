"""DTO модуля tenancy (часть OpenAPI-спеки)."""

from __future__ import annotations

import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    created_by: uuid.UUID


class WorkspaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_by: uuid.UUID
    created_at: datetime.datetime


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    created_by: uuid.UUID


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    created_by: uuid.UUID
    created_at: datetime.datetime


class MemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    joined_at: datetime.datetime
