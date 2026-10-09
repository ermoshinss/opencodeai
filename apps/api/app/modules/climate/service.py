"""Сервис модуля climate (синтетическое состояние устройств)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.modules.climate.models import Device, Reading


def get_device(db: Session, device_id: uuid.UUID) -> Device:
    device = db.get(Device, device_id)
    if device is None:
        raise ApiError("device_not_found", "Устройство не найдено", status_code=404)
    return device


def devices_for_module(db: Session, module_node_id: uuid.UUID) -> list[Device]:
    return list(
        db.scalars(
            select(Device)
            .where(Device.module_node_id == module_node_id)
            .order_by(Device.created_at)
        )
    )


def devices_for_home(db: Session, home_id: uuid.UUID) -> list[Device]:
    from app.modules.tenancy.models import Resource

    module_ids = list(
        db.scalars(
            select(Resource.id).where(
                Resource.home_id == home_id,
                Resource.node_type == "module",
                Resource.module_code == "climate",
            )
        )
    )
    if not module_ids:
        return []
    return list(db.scalars(select(Device).where(Device.module_node_id.in_(module_ids))))


def create_device(
    db: Session,
    node_id: uuid.UUID,
    module_node_id: uuid.UUID,
    name: str,
    kind: str,
) -> Device:
    defaults = {
        "sensor": {"mode": "idle", "temp": 21.0, "hum": 45.0},
        "controller": {"mode": "auto", "target_temp": 22.0},
    }
    device = Device(
        id=node_id,
        module_node_id=module_node_id,
        name=name,
        kind=kind,
        state=defaults.get(kind, {"mode": "idle"}),
    )
    db.add(device)
    db.flush()
    db.add(Reading(device_id=device.id, metric="temp", value=21.0))
    if kind == "sensor":
        db.add(Reading(device_id=device.id, metric="hum", value=45.0))
    db.commit()
    db.refresh(device)
    return device


def list_readings(db: Session, device_id: uuid.UUID, limit: int = 100) -> list[Reading]:
    return list(
        db.scalars(
            select(Reading)
            .where(Reading.device_id == device_id)
            .order_by(Reading.created_at.desc())
            .limit(limit)
        )
    )


_COMMANDS = {"power", "set_target", "heat", "cool"}


def apply_command(db: Session, device: Device, command: str, params: dict) -> Device:
    if command not in _COMMANDS:
        raise ApiError("unknown_command", f"Команда '{command}' не поддерживается", status_code=400)
    state = dict(device.state or {})
    if command == "power":
        state["mode"] = "on" if params.get("on", True) else "off"
    elif command == "set_target":
        target = params.get("target_temp")
        if not isinstance(target, (int, float)):
            raise ApiError("bad_param", "Параметр target_temp обязателен", status_code=400)
        state["target_temp"] = float(target)
        state["mode"] = "auto"
    elif command == "heat":
        state["mode"] = "heat"
    elif command == "cool":
        state["mode"] = "cool"
    device.state = state
    target = state.get("target_temp")
    recorded = float(target) if isinstance(target, (int, float)) else 1.0
    db.add(Reading(device_id=device.id, metric=command, value=recorded))
    db.commit()
    db.refresh(device)
    return device