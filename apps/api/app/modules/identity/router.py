"""Эндпоинты аутентификации и текущего пользователя."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.security.http import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.identity import service
from app.modules.identity.models import User
from app.modules.identity.schemas import (
    LoginIn,
    MeOut,
    RegisterIn,
    TokenOut,
    UserRead,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(data: RegisterIn, db: Session = Depends(get_db)) -> User:
    return service.register(db, data)


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    user = service.authenticate(db, data)
    return TokenOut(access_token=service.create_session(db, user))


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(service.get_current_user)],
)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(service.get_credentials),
    db: Session = Depends(get_db),
) -> None:
    service.revoke_session(db, credentials.credentials)


@router.get("/me", response_model=MeOut)
def me(user: User = Depends(service.get_current_user), db: Session = Depends(get_db)) -> MeOut:
    return service.build_me(db, user)