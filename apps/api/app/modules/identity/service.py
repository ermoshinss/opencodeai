"""Сервис модуля identity."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.modules.identity.models import User
from app.modules.identity.schemas import UserCreate


def create_user(db: Session, data: UserCreate) -> User:
    existing = db.scalar(select(User).where(User.email == data.email))
    if existing is not None:
        raise ApiError("email_exists", "Пользователь с таким email уже существует", status_code=409)
    user = User(email=data.email, name=data.name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: uuid.UUID) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise ApiError("user_not_found", "Пользователь не найден", status_code=404)
    return user


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at)))
