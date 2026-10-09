"""DTO модуля identity (часть OpenAPI-спеки)."""

from __future__ import annotations

import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    name: str = Field(min_length=1, max_length=200)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    name: str
    created_at: datetime.datetime


class RegisterIn(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=8, max_length=200)


class LoginIn(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=200)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class HomeBrief(BaseModel):
    id: uuid.UUID
    name: str
    rights: list[str]


class MeOut(BaseModel):
    user: UserRead
    homes: list[HomeBrief]