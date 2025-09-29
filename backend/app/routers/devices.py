from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from app.models.schemas import Device, DeviceAction, DeviceCreate, DeviceUpdate
from app.services.auth import get_current_user, require_admin
from app.services.iot_simulation import device_simulator
from app.storage.json_storage import storage

router = APIRouter()


@router.get("/devices", response_model=List[Device])
async def get_devices(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> List[Device]:
    """Get all devices with their current status."""
    devices = storage.get_devices()

    devices_status: List[Dict[str, Any]] = []
    for device_data in devices:
        device_simulator.register_device(device_data)
        simulated_status = device_simulator.get_device_status(device_data["id"]) or {}
        combined = {**device_data, **simulated_status}
        devices_status.append(combined)

    return devices_status


@router.get("/devices/{device_id}", response_model=Device)
async def get_device(
    device_id: int, current_user: Dict[str, Any] = Depends(get_current_user)
) -> Device:
    """Get specific device details."""
    device_data = storage.get_device_by_id(device_id)
    if not device_data:
        raise HTTPException(status_code=404, detail="Device not found")

    device_simulator.register_device(device_data)
    simulated_status = device_simulator.get_device_status(device_id) or {}
    return {**device_data, **simulated_status}


@router.post(
    "/devices",
    response_model=Device,
    status_code=status.HTTP_201_CREATED,
)
async def create_device(
    device: DeviceCreate, admin_user: Dict[str, Any] = Depends(require_admin)
) -> Device:
    """Create a new IoT device (admin only)."""
    payload = device.model_dump()

    if payload.get("resource_id"):
        resource = storage.get_resource_by_id(payload["resource_id"])
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")

    new_device = storage.add_device(payload)
    device_simulator.register_device(new_device)
    return new_device


@router.put("/devices/{device_id}", response_model=Device)
async def update_device(
    device_id: int,
    updates: DeviceUpdate,
    admin_user: Dict[str, Any] = Depends(require_admin),
) -> Device:
    """Update device information (admin only)."""
    if not storage.get_device_by_id(device_id):
        raise HTTPException(status_code=404, detail="Device not found")

    data = updates.model_dump(exclude_unset=True)

    if "resource_id" in data and data["resource_id"] is not None:
        resource = storage.get_resource_by_id(data["resource_id"])
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")

    storage.update_device(device_id, data)
    updated_device = storage.get_device_by_id(device_id)
    if updated_device:
        device_simulator.register_device(updated_device)
        simulated_status = device_simulator.get_device_status(device_id) or {}
        return {**updated_device, **simulated_status}

    raise HTTPException(status_code=404, detail="Device not found")


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: int, admin_user: Dict[str, Any] = Depends(require_admin)
) -> None:
    """Delete a device (admin only)."""
    if not storage.delete_device(device_id):
        raise HTTPException(status_code=404, detail="Device not found")


@router.post("/devices/{device_id}/action")
async def execute_device_action(
    device_id: int,
    action_request: DeviceAction,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Execute action on IoT device."""
    device_data = storage.get_device_by_id(device_id)
    if not device_data:
        raise HTTPException(status_code=404, detail="Device not found")

    device_simulator.register_device(device_data)

    result = device_simulator.execute_device_action(
        device_id, action_request.action
    )

    if result.get("success"):
        updates: Dict[str, Any] = {"status": result.get("status")}
        if "value" in result:
            updates["value"] = result["value"]

        storage.update_device(device_id, updates)

    return result
