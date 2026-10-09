"""Синтетические тесты RBAC: матрица прав, наследование, изоляция."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

from tests import helpers

client = TestClient(app)


@pytest.fixture(scope="module")
def ctx() -> dict:
    helpers.register(client, "rbac-alice@test.local", "Alice")
    helpers.register(client, "rbac-bob@test.local", "Bob")
    helpers.register(client, "rbac-carol@test.local", "Carol")
    helpers.register(client, "rbac-dave@test.local", "Dave")
    helpers.register(client, "rbac-eve@test.local", "Eve")

    alice = helpers.login(client, "rbac-alice@test.local")
    dave = helpers.login(client, "rbac-dave@test.local")

    home_a = helpers.create_home(client, alice, "Дом Алисы")
    helpers.create_home(client, dave, "Дом Дэйва")
    module = helpers.enable_module(client, alice, uuid.UUID(home_a["id"]), "climate")

    helpers.assign_role(client, alice, uuid.UUID(home_a["id"]), "rbac-bob@test.local", "admin")
    helpers.assign_role(
        client,
        alice,
        uuid.UUID(home_a["id"]),
        "rbac-carol@test.local",
        "user",
        uuid.UUID(module["id"]),
    )
    device = helpers.create_device(client, alice, uuid.UUID(home_a["id"]), "Контролер А", "controller")

    home_b = client.get("/api/v1/homes", headers=helpers.auth(dave)).json()[0]

    return {
        "alice": alice,
        "dave": dave,
        "home_a": uuid.UUID(home_a["id"]),
        "home_b": uuid.UUID(home_b["id"]),
        "module": uuid.UUID(module["id"]),
        "device": uuid.UUID(device["id"]),
    }


def test_owner_rights_and_creator_assignment(ctx: dict) -> None:
    alice = ctx["alice"]

    me = client.get("/api/v1/auth/me", headers=helpers.auth(alice)).json()
    home_a = next(h for h in me["homes"] if h["id"] == str(ctx["home_a"]))
    assert "edit" in home_a["rights"]
    assert "view" in home_a["rights"]

    roles = client.get(f"/api/v1/homes/{ctx['home_a']}/roles", headers=helpers.auth(alice))
    assert roles.status_code == 200, roles.text
    emails = {r["email"] for r in roles.json()}
    assert {"rbac-alice@test.local", "rbac-bob@test.local"} <= emails


def test_admin_can_edit_but_not_manage_roles(ctx: dict) -> None:
    bob = helpers.login(client, "rbac-bob@test.local")

    module_node = client.get(
        f"/api/v1/homes/{ctx['home_a']}/modules/{ctx['module']}/submodules",
        headers=helpers.auth(bob),
    )
    assert module_node.status_code == 200

    device = client.post(
        f"/api/v1/homes/{ctx['home_a']}/climate/devices",
        json={"name": "Датчик Боба", "kind": "sensor"},
        headers=helpers.auth(bob),
    )
    assert device.status_code == 201, device.text

    roles = client.post(
        f"/api/v1/homes/{ctx['home_a']}/roles",
        json={"email": "rbac-eve@test.local", "role_code": "user"},
        headers=helpers.auth(bob),
    )
    assert roles.status_code == 403


def test_view_only_inheritance_and_edit_denied(ctx: dict) -> None:
    carol = helpers.login(client, "rbac-carol@test.local")

    home = client.get(f"/api/v1/homes/{ctx['home_a']}", headers=helpers.auth(carol))
    assert home.status_code == 200

    readings = client.get(
        f"/api/v1/homes/{ctx['home_a']}/climate/devices/{ctx['device']}/readings",
        headers=helpers.auth(carol),
    )
    assert readings.status_code == 200, readings.text

    command = client.post(
        f"/api/v1/homes/{ctx['home_a']}/climate/devices/{ctx['device']}/command",
        json={"command": "power", "params": {"on": False}},
        headers=helpers.auth(carol),
    )
    assert command.status_code == 403

    device = client.post(
        f"/api/v1/homes/{ctx['home_a']}/climate/devices",
        json={"name": "Нет", "kind": "sensor"},
        headers=helpers.auth(carol),
    )
    assert device.status_code == 403


def test_cross_home_isolation(ctx: dict) -> None:
    home_a = client.get(f"/api/v1/homes/{ctx['home_a']}", headers=helpers.auth(ctx["dave"]))
    assert home_a.status_code == 403

    modules = client.get(
        f"/api/v1/homes/{ctx['home_a']}/modules",
        headers=helpers.auth(ctx["dave"]),
    )
    assert modules.status_code == 403

    me = client.get("/api/v1/auth/me", headers=helpers.auth(ctx["dave"])).json()
    assert {h["id"] for h in me["homes"]} == {str(ctx["home_b"])}


def test_subnode_eligibility_adds_home(ctx: dict) -> None:
    alice = ctx["alice"]

    helpers.assign_role(
        client,
        alice,
        ctx["home_a"],
        "rbac-eve@test.local",
        "user",
        ctx["device"],
    )
    eve = helpers.login(client, "rbac-eve@test.local")

    me = client.get("/api/v1/auth/me", headers=helpers.auth(eve)).json()
    assert {h["id"] for h in me["homes"]} == {str(ctx["home_a"])}
    assert me["homes"][0]["rights"] == ["view"]

    device = client.get(
        f"/api/v1/homes/{ctx['home_a']}/climate/devices/{ctx['device']}",
        headers=helpers.auth(eve),
    )
    assert device.status_code == 200


def test_superadmin_bypass_and_admin_api(ctx: dict) -> None:
    sa = helpers.superadmin_token(client)

    users = client.get("/api/v1/admin/users", headers=helpers.auth(sa))
    assert users.status_code == 200
    assert any(u["email"] == "rbac-alice@test.local" for u in users.json())

    roles = client.get("/api/v1/admin/roles", headers=helpers.auth(sa))
    assert roles.status_code == 200
    codes = {r["code"] for r in roles.json()}
    assert {"superadmin", "owner", "admin", "user"} <= codes

    homes = client.get("/api/v1/admin/homes", headers=helpers.auth(sa))
    assert homes.status_code == 200
    home_ids = {h["id"] for h in homes.json()}
    assert {str(ctx["home_a"]), str(ctx["home_b"])} <= home_ids

    cross = client.post(
        f"/api/v1/homes/{ctx['home_a']}/roles",
        json={"email": "rbac-dave@test.local", "role_code": "admin"},
        headers=helpers.auth(sa),
    )
    assert cross.status_code == 201, cross.text


def test_admin_api_denied_for_regular_user(ctx: dict) -> None:
    del ctx
    eve = helpers.login(client, "rbac-eve@test.local")
    response = client.get("/api/v1/admin/users", headers=helpers.auth(eve))
    assert response.status_code == 403

    anon = client.get("/api/v1/admin/users")
    assert anon.status_code == 401


def test_superadmin_grant_cycle(ctx: dict) -> None:
    del ctx
    sa = helpers.superadmin_token(client)
    alice_user = next(
        u for u in client.get("/api/v1/admin/users", headers=helpers.auth(sa)).json()
        if u["email"] == "rbac-alice@test.local"
    )
    grant = client.post(
        f"/api/v1/admin/users/{alice_user['id']}/superadmin",
        headers=helpers.auth(sa),
    )
    assert grant.status_code == 201, grant.text

    alice = helpers.login(client, "rbac-alice@test.local")
    users = client.get("/api/v1/admin/users", headers=helpers.auth(alice))
    assert users.status_code == 200

    revoke = client.delete(
        f"/api/v1/admin/users/{alice_user['id']}/superadmin",
        headers=helpers.auth(sa),
    )
    assert revoke.status_code == 204