"""Синтетические тесты вертикали climate: устройства, показания, команды."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

from tests import helpers

client = TestClient(app)


@pytest.fixture(scope="module")
def setup() -> dict:
    helpers.register(client, "cl-owner@test.local", "Clima Owner")
    owner = helpers.login(client, "cl-owner@test.local")
    home = helpers.create_home(client, owner, "Климат-дом")
    home_id = uuid.UUID(home["id"])
    return {"owner": owner, "home_id": home_id}


def test_module_not_enabled_404(setup: dict) -> None:
    response = client.get(
        f"/api/v1/homes/{setup['home_id']}/climate/devices",
        headers=helpers.auth(setup["owner"]),
    )
    assert response.status_code == 404
    assert response.json()["code"] == "module_not_enabled"


def test_enable_and_create_devices(setup: dict) -> None:
    owner = setup["owner"]
    home_id = setup["home_id"]
    helpers.enable_module(client, owner, home_id, "climate")

    controller = helpers.create_device(client, owner, home_id, "Термостат", "controller")
    sensor = helpers.create_device(client, owner, home_id, "Датчик", "sensor")

    assert controller["kind"] == "controller"
    assert controller["state"]["target_temp"] == 22.0
    assert sensor["state"]["temp"] == 21.0

    devices = client.get(
        f"/api/v1/homes/{home_id}/climate/devices",
        headers=helpers.auth(owner),
    )
    assert devices.status_code == 200
    assert {d["id"] for d in devices.json()} == {controller["id"], sensor["id"]}


def test_readings_and_command(setup: dict) -> None:
    owner = setup["owner"]
    home_id = setup["home_id"]

    devices = client.get(
        f"/api/v1/homes/{home_id}/climate/devices",
        headers=helpers.auth(owner),
    ).json()
    controller = next(d for d in devices if d["kind"] == "controller")

    readings = client.get(
        f"/api/v1/homes/{home_id}/climate/devices/{controller['id']}/readings",
        headers=helpers.auth(owner),
    )
    assert readings.status_code == 200
    assert any(r["metric"] == "temp" for r in readings.json())

    command = client.post(
        f"/api/v1/homes/{home_id}/climate/devices/{controller['id']}/command",
        json={"command": "set_target", "params": {"target_temp": 23.5}},
        headers=helpers.auth(owner),
    )
    assert command.status_code == 200, command.text
    assert command.json()["state"]["target_temp"] == 23.5

    power = client.post(
        f"/api/v1/homes/{home_id}/climate/devices/{controller['id']}/command",
        json={"command": "power", "params": {"on": False}},
        headers=helpers.auth(owner),
    )
    assert power.status_code == 200
    assert power.json()["state"]["mode"] == "off"

    unknown = client.post(
        f"/api/v1/homes/{home_id}/climate/devices/{controller['id']}/command",
        json={"command": "explode", "params": {}},
        headers=helpers.auth(owner),
    )
    assert unknown.status_code == 400
    assert unknown.json()["code"] == "unknown_command"


def test_status_aggregate(setup: dict) -> None:
    owner = setup["owner"]
    home_id = setup["home_id"]
    status = client.get(
        f"/api/v1/homes/{home_id}/climate/status",
        headers=helpers.auth(owner),
    )
    assert status.status_code == 200, status.text
    body = status.json()
    assert body["device_count"] == 2
    assert body["enabled"] is True


def test_device_rbac_edit_required(setup: dict) -> None:
    helpers.register(client, "cl-viewer@test.local", "Clima Viewer")
    owner = setup["owner"]
    home_id = setup["home_id"]

    devices = client.get(
        f"/api/v1/homes/{home_id}/climate/devices",
        headers=helpers.auth(owner),
    ).json()
    controller = next(d for d in devices if d["kind"] == "controller")

    helpers.assign_role(client, owner, home_id, "cl-viewer@test.local", "user", uuid.UUID(controller["id"]))
    viewer = helpers.login(client, "cl-viewer@test.local")

    readings = client.get(
        f"/api/v1/homes/{home_id}/climate/devices/{controller['id']}/readings",
        headers=helpers.auth(viewer),
    )
    assert readings.status_code == 200

    command = client.post(
        f"/api/v1/homes/{home_id}/climate/devices/{controller['id']}/command",
        json={"command": "power", "params": {"on": True}},
        headers=helpers.auth(viewer),
    )
    assert command.status_code == 403