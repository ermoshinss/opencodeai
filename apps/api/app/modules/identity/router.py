"""Эндпоинты модуля identity (dev-режим, авторизация ещё не включена)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.identity import service
from app.modules.identity.models import User
from app.modules.identity.schemas import UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["identity"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(data: UserCreate, db: Session = Depends(get_db)) -> User:
    return service.create_user(db, data)


@router.get("", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)) -> list[User]:
    return service.list_users(db)


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)) -> User:
    return service.get_user(db, user_id)
