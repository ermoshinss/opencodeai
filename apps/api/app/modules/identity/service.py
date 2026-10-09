"""Сервис модуля identity: пользователи, пароли, сессии, current_user."""

from __future__ import annotations

import datetime
import uuid

from fastapi import Depends
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import security
from app.core.db import get_db
from app.core.errors import ApiError
from app.modules.authorization import service as authz_service
from app.modules.identity.models import Session as IdentitySession
from app.modules.identity.models import User
from app.modules.identity.schemas import HomeBrief, LoginIn, MeOut, RegisterIn, UserRead

SESSION_TTL = datetime.timedelta(days=30)
_bearer = HTTPBearer(auto_error=False)


def get_user(db: Session, user_id: uuid.UUID) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise ApiError("user_not_found", "Пользователь не найден", status_code=404)
    return user


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at)))


def register(db: Session, data: RegisterIn) -> User:
    if get_user_by_email(db, data.email) is not None:
        raise ApiError("email_exists", "Пользователь с таким email уже существует", status_code=409)
    user = User(
        email=data.email,
        name=data.name,
        password_hash=security.hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, data: LoginIn) -> User:
    user = get_user_by_email(db, data.email)
    if user is None or user.password_hash is None:
        raise ApiError("invalid_credentials", "Неверный email или пароль", status_code=401)
    if not security.verify_password(data.password, user.password_hash):
        raise ApiError("invalid_credentials", "Неверный email или пароль", status_code=401)
    return user


def create_session(db: Session, user: User) -> str:
    raw = security.new_session_token()
    session = IdentitySession(
        user_id=user.id,
        token_hash=security.sha256_hex(raw),
        expires_at=datetime.datetime.now(datetime.UTC) + SESSION_TTL,
    )
    db.add(session)
    db.commit()
    return raw


def get_session_user(db: Session, raw_token: str) -> User | None:
    token_hash = security.sha256_hex(raw_token)
    session = db.scalar(
        select(IdentitySession).where(
            IdentitySession.token_hash == token_hash,
            IdentitySession.revoked_at.is_(None),
            IdentitySession.expires_at > datetime.datetime.now(datetime.UTC),
        )
    )
    if session is None:
        return None
    return db.get(User, session.user_id)


def revoke_session(db: Session, raw_token: str) -> None:
    token_hash = security.sha256_hex(raw_token)
    session = db.scalar(select(IdentitySession).where(IdentitySession.token_hash == token_hash))
    if session is not None and session.revoked_at is None:
        session.revoked_at = datetime.datetime.now(datetime.UTC)
        session.expires_at = datetime.datetime.now(datetime.UTC)
        db.commit()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise ApiError("auth_required", "Требуется авторизация", status_code=401)
    user = get_session_user(db, credentials.credentials)
    if user is None:
        raise ApiError("invalid_token", "Сессия недействительна или истекла", status_code=401)
    return user


def get_credentials(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> HTTPAuthorizationCredentials:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise ApiError("auth_required", "Требуется авторизация", status_code=401)
    return credentials


def build_me(db: Session, user: User) -> MeOut:
    homes = []
    for home in authz_service.my_homes(db, user.id):
        rights = sorted(authz_service.home_rights_for_me(db, user.id, home))
        homes.append(HomeBrief(id=home.id, name=home.name, rights=rights))

    return MeOut(user=UserRead.model_validate(user), homes=homes)