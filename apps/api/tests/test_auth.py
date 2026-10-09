"""Синтетические тесты аутентификации и сессий."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

from tests import helpers

client = TestClient(app)


def test_register_login_me_logout() -> None:
    user = helpers.register(client, "u-auth@test.local", "Auth User")
    token = helpers.login(client, "u-auth@test.local")
    assert token

    me = client.get("/api/v1/auth/me", headers=helpers.auth(token))
    assert me.status_code == 200, me.text
    body = me.json()
    assert body["user"]["id"] == user["id"]
    assert body["user"]["email"] == "u-auth@test.local"
    assert body["homes"] == []

    logout = client.post("/api/v1/auth/logout", headers=helpers.auth(token))
    assert logout.status_code == 204

    after = client.get("/api/v1/auth/me", headers=helpers.auth(token))
    assert after.status_code == 401
    assert after.json()["code"] == "invalid_token"


def test_login_wrong_password() -> None:
    helpers.register(client, "u-badpass@test.local", "Bad Pass")
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "u-badpass@test.local", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_credentials"


def test_me_without_token() -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["code"] == "auth_required"


def test_register_duplicate_email_conflicts() -> None:
    helpers.register(client, "u-dupe@test.local", "First")
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "u-dupe@test.local", "name": "Second", "password": helpers.PASSWORD},
    )
    assert response.status_code == 409
    assert response.json()["code"] == "email_exists"


def test_register_short_password() -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "u-short@test.local", "name": "Short", "password": "short"},
    )
    assert response.status_code == 422