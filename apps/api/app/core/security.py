"""Криптография и токены для аутентификации (инфраструктура).

Формат пароля: `pbkdf2_sha256$iterations$salt_hex$hash_hex`.
Токен сессии — случайный hex; в БД хранится только sha256 (см. identity).
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets

PBKDF2_ITERATIONS = 260_000
_PBKDF2 = "pbkdf2_sha256"


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return f"{_PBKDF2}${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    parts = stored.split("$")
    if len(parts) != 4 or parts[0] != _PBKDF2:
        return False
    try:
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected = bytes.fromhex(parts[3])
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(digest, expected)


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def new_session_token() -> str:
    return secrets.token_hex(32)