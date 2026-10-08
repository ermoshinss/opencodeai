"""Сквозной сценарий: пользователь → workspace → проект → доступ к модулю."""

from __future__ import annotations

import uuid

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def _create_user(email: str, name: str) -> uuid.UUID:
    response = client.post("/api/v1/users", json={"email": email, "name": name})
    assert response.status_code == 201, response.text
    return uuid.UUID(response.json()["id"])


def test_end_to_end_module_grant() -> None:
    owner = _create_user("owner@example.com", "Owner")

    workspace_response = client.post(
        "/api/v1/workspaces", json={"name": "Умный дом", "created_by": str(owner)}
    )
    assert workspace_response.status_code == 201, workspace_response.text
    workspace_id = uuid.UUID(workspace_response.json()["id"])

    project_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/projects",
        json={"name": "Освещение", "created_by": str(owner)},
    )
    assert project_response.status_code == 201, project_response.text
    assert project_response.json()["workspace_id"] == str(workspace_id)

    modules = client.get("/api/v1/modules")
    assert modules.status_code == 200
    assert {"code", "title", "version", "state"} <= set(modules.json()[0].keys())
    assert any(m["code"] == "mail" for m in modules.json())

    grant_response = client.post(
        f"/api/v1/admin/workspaces/{workspace_id}/modules",
        json={"module_code": "mail", "enabled": True},
    )
    assert grant_response.status_code == 201, grant_response.text
    assert grant_response.json()["enabled"] is True

    grants = client.get("/api/v1/admin/grants")
    assert grants.status_code == 200
    active = [
        g
        for g in grants.json()
        if g["workspace_id"] == str(workspace_id) and g["module_code"] == "mail"
    ]
    assert len(active) == 1
    assert active[0]["enabled"] is True

    admin_users = client.get("/api/v1/admin/users")
    assert admin_users.status_code == 200
    assert str(owner) in {u["id"] for u in admin_users.json()}

    admin_workspaces = client.get("/api/v1/admin/workspaces")
    assert admin_workspaces.status_code == 200
    assert str(workspace_id) in {w["id"] for w in admin_workspaces.json()}


def test_duplicate_grant_disables_and_unknown_module_fails() -> None:
    owner = _create_user("owner2@example.com", "Owner2")
    workspace_response = client.post(
        "/api/v1/workspaces", json={"name": "Климат", "created_by": str(owner)}
    )
    workspace_id = uuid.UUID(workspace_response.json()["id"])

    client.post(
        f"/api/v1/admin/workspaces/{workspace_id}/modules",
        json={"module_code": "mail", "enabled": True},
    )
    disable = client.post(
        f"/api/v1/admin/workspaces/{workspace_id}/modules",
        json={"module_code": "mail", "enabled": False},
    )
    assert disable.status_code == 201
    assert disable.json()["enabled"] is False

    unknown = client.post(
        f"/api/v1/admin/workspaces/{workspace_id}/modules",
        json={"module_code": "weather", "enabled": True},
    )
    assert unknown.status_code == 404
    assert unknown.json()["code"] == "module_not_found"


def test_duplicate_email_conflicts() -> None:
    _create_user("same@example.com", "First")
    response = client.post("/api/v1/users", json={"email": "same@example.com", "name": "Second"})
    assert response.status_code == 409
    assert response.json()["code"] == "email_exists"
