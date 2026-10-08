"""Эндпоинты модуля registry."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.registry import service
from app.modules.registry.models import Module
from app.modules.registry.schemas import ModuleRead

router = APIRouter(prefix="/modules", tags=["registry"])


@router.get("", response_model=list[ModuleRead])
def list_modules(db: Session = Depends(get_db)) -> list[Module]:
    return service.list_modules(db)
