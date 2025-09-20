from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import Resource, ReservationRequest
from app.services.auth import get_current_user
from app.services.iot_simulation import device_simulator
from app.storage.json_storage import storage

router = APIRouter()


@router.get("/resources", response_model=List[Dict[str, Any]])
async def get_resources(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get all resources with their availability status."""
    return storage.get_resources()


@router.post("/resources/{resource_id}/reserve")
async def reserve_resource(
    resource_id: int,
    reservation_request: ReservationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Reserve a resource."""
    resource = storage.get_resource_by_id(resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    if not resource["available"]:
        raise HTTPException(
            status_code=400, detail="Resource is already reserved"
        )

    # Update resource availability
    updates = {"available": False, "reserved_by": reservation_request.user_id}
    storage.update_resource(resource_id, updates)

    # If resource has an associated device, unlock it
    if resource.get("device_id"):
        device_data = storage.get_device_by_id(resource["device_id"])
        if device_data and device_data["type"] == "lock":
            device_simulator.register_device(device_data)
            result = device_simulator.execute_device_action(
                resource["device_id"], "unlock"
            )

            if result.get("success"):
                storage.update_device(
                    resource["device_id"], {"status": result.get("status")}
                )

    # Create reservation record
    reservation = {
        "resource_id": resource_id,
        "user_id": reservation_request.user_id,
        "status": "active",
    }
    storage.add_reservation(reservation)

    return {
        "success": True,
        "message": f"Resource '{resource['name']}' reserved successfully",
        "resource_id": resource_id,
    }


@router.post("/resources/{resource_id}/release")
async def release_resource(
    resource_id: int, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Release a reserved resource."""
    resource = storage.get_resource_by_id(resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    if resource["available"]:
        raise HTTPException(status_code=400, detail="Resource is not reserved")

    # Check if current user can release this resource
    user_id = current_user["id"]
    if resource["reserved_by"] != user_id and current_user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="You can only release resources you have reserved",
        )

    # Update resource availability
    updates = {"available": True, "reserved_by": None}
    storage.update_resource(resource_id, updates)

    # If resource has an associated device, lock it
    if resource.get("device_id"):
        device_data = storage.get_device_by_id(resource["device_id"])
        if device_data and device_data["type"] == "lock":
            device_simulator.register_device(device_data)
            result = device_simulator.execute_device_action(
                resource["device_id"], "lock"
            )

            if result.get("success"):
                storage.update_device(
                    resource["device_id"], {"status": result.get("status")}
                )

    return {
        "success": True,
        "message": f"Resource '{resource['name']}' released successfully",
        "resource_id": resource_id,
    }
