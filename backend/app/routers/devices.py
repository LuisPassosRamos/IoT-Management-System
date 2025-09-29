from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.db_models import Device, DeviceType, User, UserRole
from app.models.schemas import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    DeviceActionRequest,
    DeviceStatusReport,
    DeviceCommandResponse,
)
from app.services.auth import require_active_user, require_admin
from app.services import audit, device_commands
from app.services.notifications import manager as notification_manager

router = APIRouter()


def _serialize_device(device: Device) -> DeviceResponse:
    return DeviceResponse(
        id=device.id,
        name=device.name,
        type=device.type.value,
        status=device.status,
        resource_id=device.resource_id,
        numeric_value=device.numeric_value,
        text_value=device.text_value,
        metadata=device.metadata_json,
        last_reported_at=device.last_reported_at,
    )


@router.get("/devices", response_model=List[DeviceResponse])
async def list_devices(
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db),
) -> List[DeviceResponse]:
    """List devices accessible to the user."""

    query = select(Device).options(selectinload(Device.resource)).order_by(Device.name)
    if current_user.role != UserRole.ADMIN:
        permitted_ids = [perm.resource_id for perm in current_user.permissions]
        if not permitted_ids:
            return []
        query = query.where(Device.resource_id.in_(permitted_ids))

    devices = db.scalars(query).unique().all()
    return [_serialize_device(device) for device in devices]


@router.get("/devices/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db),
) -> DeviceResponse:
    """Retrieve a single device."""

    device = db.scalar(
        select(Device)
        .options(selectinload(Device.resource))
        .where(Device.id == device_id)
    )
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    if device.resource_id and current_user.role != UserRole.ADMIN:
        permitted_ids = {perm.resource_id for perm in current_user.permissions}
        if device.resource_id not in permitted_ids:
            raise HTTPException(status_code=403, detail="Access denied")

    return _serialize_device(device)


@router.post("/devices", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    payload: DeviceCreate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> DeviceResponse:
    """Create a new device (admin only)."""

    device = Device(
        name=payload.name,
        type=DeviceType(payload.type),
        status=payload.status or "inactive",
        resource_id=payload.resource_id,
        numeric_value=payload.numeric_value,
        text_value=payload.text_value,
        metadata_json=payload.metadata,
    )
    db.add(device)
    db.flush()

    audit.record_audit(
        db,
        action="device_created",
        user_id=admin_user.id,
        device_id=device.id,
        resource_id=device.resource_id,
    )
    notification_manager.schedule_broadcast(
        {
            "type": "device.created",
            "deviceId": device.id,
            "status": device.status,
            "resourceId": device.resource_id,
        }
    )

    return _serialize_device(device)


@router.put("/devices/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    payload: DeviceUpdate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> DeviceResponse:
    """Update device information (admin only)."""

    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    updates = payload.model_dump(exclude_unset=True)
    if "type" in updates and updates["type"] is not None:
        device.type = DeviceType(updates.pop("type"))
    if "metadata" in updates:
        device.metadata_json = updates.pop("metadata")

    for attr, value in updates.items():
        setattr(device, attr, value)

    audit.record_audit(
        db,
        action="device_updated",
        user_id=admin_user.id,
        device_id=device.id,
        resource_id=device.resource_id,
    )
    notification_manager.schedule_broadcast(
        {
            "type": "device.updated",
            "deviceId": device.id,
            "status": device.status,
            "resourceId": device.resource_id,
        }
    )

    return _serialize_device(device)


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    """Delete a device (admin only)."""

    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    audit.record_audit(
        db,
        action="device_deleted",
        user_id=admin_user.id,
        device_id=device.id,
        resource_id=device.resource_id,
    )
    notification_manager.schedule_broadcast(
        {
            "type": "device.deleted",
            "deviceId": device.id,
        }
    )

    db.delete(device)


@router.post("/devices/{device_id}/actions", response_model=DeviceResponse)
async def execute_device_action(
    device_id: int,
    request: DeviceActionRequest,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db),
) -> DeviceResponse:
    """Execute a simulated action on a device."""

    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    if device.resource:
        if current_user.role != UserRole.ADMIN:
            permitted_ids = {perm.resource_id for perm in current_user.permissions}
            if device.resource_id not in permitted_ids:
                raise HTTPException(status_code=403, detail="Access denied to device")

    action = request.action.lower()
    if device.type == DeviceType.LOCK:
        if action not in {"lock", "unlock"}:
            raise HTTPException(status_code=400, detail="Unsupported action for lock device")
        device.status = "locked" if action == "lock" else "unlocked"
    elif device.type == DeviceType.SENSOR:
        if action == "read" and request.payload:
            value = request.payload.get("numeric_value")
            if value is not None:
                device.numeric_value = float(value)
        elif action in {"activate", "deactivate"}:
            device.status = "active" if action == "activate" else "inactive"
        else:
            raise HTTPException(status_code=400, detail="Unsupported action for sensor device")
    else:
        device.status = request.payload.get("status", device.status) if request.payload else device.status

    device.last_reported_at = datetime.utcnow()

    audit.record_audit(
        db,
        action="device_action",
        user_id=current_user.id,
        device_id=device.id,
        resource_id=device.resource_id,
        details={"action": action},
    )
    notification_manager.schedule_broadcast(
        {
            "type": "device.updated",
            "deviceId": device.id,
            "status": device.status,
            "resourceId": device.resource_id,
        }
    )

    return _serialize_device(device)


@router.post("/devices/{device_id}/commands/next", response_model=DeviceCommandResponse)
async def fetch_next_command(
    device_id: int,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db),
):
    """Return the next pending command for a device."""

    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    if device.resource and current_user.role != UserRole.ADMIN:
        permitted_ids = {perm.resource_id for perm in current_user.permissions}
        if device.resource_id not in permitted_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to device")

    command = device_commands.fetch_next_command(db, device_id)
    if not command:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return command


@router.post("/devices/report", status_code=status.HTTP_204_NO_CONTENT)
async def report_device_status(
    report: DeviceStatusReport,
    db: Session = Depends(get_db),
) -> None:
    """Endpoint for device simulators to send status updates."""

    device = db.get(Device, report.device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    device.status = report.status
    device.numeric_value = report.numeric_value
    device.text_value = report.text_value
    device.metadata_json = report.metadata or device.metadata_json
    device.last_reported_at = datetime.utcnow()

    audit.record_audit(
        db,
        action="device_status_report",
        device_id=device.id,
        resource_id=device.resource_id,
        details={
            "status": report.status,
            "numeric_value": report.numeric_value,
            "text_value": report.text_value,
        },
    )
    notification_manager.schedule_broadcast(
        {
            "type": "device.updated",
            "deviceId": device.id,
            "status": device.status,
            "resourceId": device.resource_id,
        }
    )
