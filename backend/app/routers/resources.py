from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from app.models.schemas import (
    Resource,
    ResourceCreate,
    ResourceUpdate,
    ReservationCreate,
    Reservation,
)
from app.services.auth import get_current_user, require_admin
from app.services.iot_simulation import device_simulator
from app.storage.json_storage import storage

router = APIRouter()


@router.get("/resources", response_model=List[Resource])
async def get_resources(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> List[Resource]:
    """Get all resources with their availability status."""
    return storage.get_resources()


@router.post(
    "/resources",
    response_model=Resource,
    status_code=status.HTTP_201_CREATED,
)
async def create_resource(
    resource: ResourceCreate, admin_user: Dict[str, Any] = Depends(require_admin)
) -> Resource:
    """Create a new resource (admin only)."""
    payload = resource.model_dump()

    device_id = payload.get("device_id")
    if device_id:
        device = storage.get_device_by_id(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        storage.update_device(device_id, {"resource_id": None})

    new_resource = storage.add_resource(payload)

    if device_id:
        storage.update_device(device_id, {"resource_id": new_resource["id"]})

    return new_resource


@router.put("/resources/{resource_id}", response_model=Resource)
async def update_resource(
    resource_id: int,
    updates: ResourceUpdate,
    admin_user: Dict[str, Any] = Depends(require_admin),
) -> Resource:
    """Update resource details (admin only)."""
    existing = storage.get_resource_by_id(resource_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Resource not found")

    data = updates.model_dump(exclude_unset=True)

    if "device_id" in data and data["device_id"] is not None:
        device = storage.get_device_by_id(data["device_id"])
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

    storage.update_resource(resource_id, data)

    if "device_id" in data:
        previous_device_id = existing.get("device_id")
        new_device_id = data["device_id"]
        if previous_device_id and previous_device_id != new_device_id:
            storage.update_device(previous_device_id, {"resource_id": None})
        if new_device_id:
            storage.update_device(new_device_id, {"resource_id": resource_id})

    updated = storage.get_resource_by_id(resource_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Resource not found")

    return updated


@router.delete("/resources/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(
    resource_id: int, admin_user: Dict[str, Any] = Depends(require_admin)
) -> None:
    """Delete a resource (admin only)."""
    if not storage.delete_resource(resource_id):
        raise HTTPException(status_code=404, detail="Resource not found")


@router.post("/resources/{resource_id}/reserve", response_model=Reservation)
async def reserve_resource(
    resource_id: int,
    reservation_request: ReservationCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Reservation:
    """Reserve a resource."""
    resource = storage.get_resource_by_id(resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    if not resource["available"]:
        raise HTTPException(
            status_code=400, detail="Resource is already reserved"
        )

    reservation_user_id = current_user["id"]
    if (
        current_user.get("role") == "admin"
        and reservation_request.user_id is not None
    ):
        reservation_user_id = reservation_request.user_id

    storage.update_resource(
        resource_id,
        {"available": False, "reserved_by": reservation_user_id},
    )

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

    reservation_payload = {
        "resource_id": resource_id,
        "user_id": reservation_user_id,
        "status": "active",
    }
    return storage.add_reservation(reservation_payload)


@router.post("/resources/{resource_id}/release", response_model=Resource)
async def release_resource(
    resource_id: int, current_user: Dict[str, Any] = Depends(get_current_user)
) -> Resource:
    """Release a reserved resource."""
    resource = storage.get_resource_by_id(resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    if resource["available"]:
        raise HTTPException(status_code=400, detail="Resource is not reserved")

    user_id = current_user["id"]
    if resource["reserved_by"] != user_id and current_user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="You can only release resources you have reserved",
        )

    storage.update_resource(
        resource_id,
        {"available": True, "reserved_by": None},
    )

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

    active_reservations = [
        reservation
        for reservation in storage.get_reservations()
        if reservation["resource_id"] == resource_id
        and reservation["status"] == "active"
    ]
    if active_reservations:
        latest = sorted(
            active_reservations, key=lambda item: item["timestamp"]
        )[-1]
        storage.update_reservation(latest["id"], {"status": "completed"})

    updated_resource = storage.get_resource_by_id(resource_id)
    if not updated_resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    return updated_resource
