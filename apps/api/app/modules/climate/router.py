"""Эндпоинты вертикали climate (поддомены /homes/{id}/climate)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import ApiError
from app.modules.authorization import service as authz_service
from app.modules.climate import service as climate_service
from app.modules.climate.models import Device
from app.modules.climate.schemas import (
    CommandIn,
    DeviceCreate,
    DeviceRead,
    DeviceStatus,
    HomeStatusOut,
    ReadingRead,
)
from app.modules.identity import service as identity_service
from app.modules.identity.models import User
from app.modules.tenancy import service as tenancy_service
from app.modules.tenancy.models import Resource

router = APIRouter(prefix="/homes/{home_id}/climate", tags=["climate"])


def _climate_module(db: Session, home_id: uuid.UUID) -> Resource:
    home = tenancy_service.get_node_checked(db, home_id, "home")
    module = db.scalar(
        select(Resource).where(
            Resource.home_id == home.id,
            Resource.node_type == "module",
            Resource.module_code == "climate",
        )
    )
    if module is None:
        raise ApiError(
            "module_not_enabled",
            "Модуль climate не включён в этом доме",
            status_code=404,
        )
    return module


def _device_read(device: Device) -> DeviceRead:
    return DeviceRead(
        id=device.id,
        name=device.name,
        kind=device.kind,
        state=device.state or {},
        created_at=device.created_at,
    )


def _reading_read(item) -> ReadingRead:
    return ReadingRead(
        id=item.id,
        metric=item.metric,
        value=item.value,
        created_at=item.created_at,
    )


@router.get("/devices", response_model=list[DeviceRead])
def list_devices(
    home_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(identity_service.get_current_user),
) -> list[DeviceRead]:
    module = _climate_module(db, home_id)
    authz_service.ensure_right(db, user.id, module.id, "view")
    return [_device_read(d) for d in climate_service.devices_for_module(db, module.id)]


@router.post("/devices", response_model=DeviceRead, status_code=status.HTTP_201_CREATED)
def create_device(
    home_id: uuid.UUID,
    data: DeviceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(identity_service.get_current_user),
) -> DeviceRead:
    module = _climate_module(db, home_id)
    authz_service.ensure_right(db, user.id, module.id, "edit")
    node = tenancy_service.create_submodule(db, module, data.name)
    device = climate_service.create_device(db, node.id, module.id, data.name, data.kind)
    return _device_read(device)


@router.get("/devices/{device_id}", response_model=DeviceRead)
def get_device(
    home_id: uuid.UUID,
    device_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(identity_service.get_current_user),
) -> DeviceRead:
    module = _climate_module(db, home_id)
    device = climate_service.get_device(db, device_id)
    if device.module_node_id != module.id:
        raise ApiError(
            "device_not_in_home",
            "Устройство не принадлежит модулю климата этого дома",
            status_code=400,
        )
    authz_service.ensure_right(db, user.id, device.id, "view")
    return _device_read(device)


@router.get("/devices/{device_id}/readings", response_model=list[ReadingRead])
def list_readings(
    home_id: uuid.UUID,
    device_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(identity_service.get_current_user),
) -> list[ReadingRead]:
    module = _climate_module(db, home_id)
    device = climate_service.get_device(db, device_id)
    if device.module_node_id != module.id:
        raise ApiError(
            "device_not_in_home",
            "Устройство не принадлежит модулю климата этого дома",
            status_code=400,
        )
    authz_service.ensure_right(db, user.id, device.id, "view")
    return [_reading_read(r) for r in climate_service.list_readings(db, device.id)]


@router.post("/devices/{device_id}/command", response_model=DeviceRead)
def device_command(
    home_id: uuid.UUID,
    device_id: uuid.UUID,
    data: CommandIn,
    db: Session = Depends(get_db),
    user: User = Depends(identity_service.get_current_user),
) -> DeviceRead:
    module = _climate_module(db, home_id)
    device = climate_service.get_device(db, device_id)
    if device.module_node_id != module.id:
        raise ApiError(
            "device_not_in_home",
            "Устройство не принадлежит модулю климата этого дома",
            status_code=400,
        )
    authz_service.ensure_right(db, user.id, device.id, "edit")
    updated = climate_service.apply_command(db, device, data.command, data.params)
    return _device_read(updated)


@router.get("/status", response_model=HomeStatusOut)
def home_status(
    home_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(identity_service.get_current_user),
) -> HomeStatusOut:
    home = tenancy_service.get_node_checked(db, home_id, "home")
    if not authz_service.can_view_home(db, user.id, home):
        raise ApiError("forbidden", "Недостаточно прав", status_code=403)
    devices = climate_service.devices_for_home(db, home.id)
    return HomeStatusOut(
        enabled=bool(devices),
        device_count=len(devices),
        devices=[
            DeviceStatus(id=d.id, name=d.name, state=d.state or {})
            for d in devices
        ],
    )