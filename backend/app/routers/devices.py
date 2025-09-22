from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import Device, DeviceAction
from app.services.auth import get_current_user
from app.services.iot_simulation import device_simulator
from app.storage.json_storage import storage

router = APIRouter()


@router.get("/devices", response_model=List[Dict[str, Any]])
async def get_devices(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get all devices with their current status."""
    devices = storage.get_devices()

    # Initialize device simulator with current devices
    for device_data in devices:
        device_simulator.register_device(device_data)

    # Get updated status from simulator
    devices_status = []
    for device_data in devices:
        simulated_status = device_simulator.get_device_status(
            device_data["id"]
        )
        if simulated_status:
            devices_status.append(simulated_status)
        else:
            devices_status.append(device_data)

    return devices_status


@router.get("/devices/{device_id}")
async def get_device(
    device_id: int, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get specific device details."""
    device_data = storage.get_device_by_id(device_id)
    if not device_data:
        raise HTTPException(status_code=404, detail="Device not found")

    # Initialize device in simulator
    device_simulator.register_device(device_data)

    # Get current status from simulator
    simulated_status = device_simulator.get_device_status(device_id)
    return simulated_status if simulated_status else device_data


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

    # Initialize device in simulator
    device_simulator.register_device(device_data)

    # Execute action
    result = device_simulator.execute_device_action(
        device_id, action_request.action
    )

    if result.get("success"):
        # Update device status in storage
        updates = {"status": result.get("status")}
        if "value" in result:
            updates["value"] = result["value"]

        storage.update_device(device_id, updates)

    return result
