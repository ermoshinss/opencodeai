"""Тестовые хелперы: регистрация, токены, дома, модули, устройства."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from tests.conftest import SUPERADMIN_EMAIL, SUPERADMIN_PASSWORD

PASSWORD = "test-password-123"


def register(client: TestClient, email: str, name: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "name": name, "password": PASSWORD},
    )
    assert response.status_code == 201, response.text
    return response.json()


def login(client: TestClient, email: str, password: str = PASSWORD) -> str:
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def superadmin_token(client: TestClient) -> str:
    return login(client, SUPERADMIN_EMAIL, SUPERADMIN_PASSWORD)


def create_home(client: TestClient, token: str, name: str) -> dict:
    response = client.post("/api/v1/homes", json={"name": name}, headers=auth(token))
    assert response.status_code == 201, response.text
    return response.json()


def enable_module(client: TestClient, token: str, home_id: uuid.UUID, code: str) -> dict:
    response = client.post(
        f"/api/v1/homes/{home_id}/modules",
        json={"module_code": code},
        headers=auth(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def assign_role(
    client: TestClient,
    token: str,
    home_id: uuid.UUID,
    email: str,
    role_code: str,
    node_id: uuid.UUID | None = None,
) -> dict:
    payload: dict = {"email": email, "role_code": role_code}
    if node_id is not None:
        payload["node_id"] = str(node_id)
    response = client.post(
        f"/api/v1/homes/{home_id}/roles", json=payload, headers=auth(token)
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_device(
    client: TestClient,
    token: str,
    home_id: uuid.UUID,
    name: str,
    kind: str,
) -> dict:
    response = client.post(
        f"/api/v1/homes/{home_id}/climate/devices",
        json={"name": name, "kind": kind},
        headers=auth(token),
    )
    assert response.status_code == 201, response.text
    return response.json()