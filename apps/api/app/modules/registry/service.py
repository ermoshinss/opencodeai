"""Сервис модуля registry."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.modules.registry.models import Module


def list_modules(db: Session) -> list[Module]:
    return list(db.scalars(select(Module).order_by(Module.code)))


def get_module_by_code(db: Session, code: str) -> Module:
    module = db.scalar(select(Module).where(Module.code == code))
    if module is None:
        raise ApiError("module_not_found", f"Модуль '{code}' не зарегистрирован", status_code=404)
    return module
