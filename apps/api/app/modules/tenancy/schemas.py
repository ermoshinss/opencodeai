"""DTO модуля tenancy (OpenAPI-контракты дерева ресурсов)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class HomeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class ResourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    home_id: uuid.UUID
    parent_id: uuid.UUID | None
    node_type: str
    module_code: str | None
    name: str
    config: dict = Field(default_factory=dict)


class ModuleEnableIn(BaseModel):
    module_code: str = Field(min_length=1, max_length=50)


class SubmoduleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class HomeRightsRead(BaseModel):
    id: uuid.UUID
    name: str
    rights: list[str]