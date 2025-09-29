from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import ReservationSummary, ReservationUpdate
from app.services.auth import require_admin
from app.storage.json_storage import storage

router = APIRouter()


def _build_reservation_summary(reservation: Dict[str, Any]) -> ReservationSummary:
    """Enrich reservation data with user and resource details."""
    resource = storage.get_resource_by_id(reservation["resource_id"])
    users = storage.get_users()
    user = next((u for u in users if u["id"] == reservation["user_id"]), None)

    return ReservationSummary(
        **reservation,
        resource_name=resource["name"] if resource else None,
        username=user["username"] if user else None,
    )


@router.get("/reservations", response_model=List[ReservationSummary])
async def list_reservations(
    admin_user: Dict[str, Any] = Depends(require_admin),
) -> List[ReservationSummary]:
    """List all reservations (admin only)."""
    reservations = storage.get_reservations()
    enriched = [_build_reservation_summary(reservation) for reservation in reservations]
    return sorted(enriched, key=lambda item: item.timestamp, reverse=True)


@router.patch("/reservations/{reservation_id}", response_model=ReservationSummary)
async def update_reservation_status(
    reservation_id: int,
    updates: ReservationUpdate,
    admin_user: Dict[str, Any] = Depends(require_admin),
) -> ReservationSummary:
    """Update reservation status (admin only)."""
    reservation = storage.get_reservation_by_id(reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    update_data = updates.model_dump(exclude_unset=True)
    if not update_data:
        return _build_reservation_summary(reservation)

    allowed_status = {"active", "completed", "cancelled"}
    if "status" in update_data and update_data["status"] not in allowed_status:
        raise HTTPException(status_code=400, detail="Invalid status value")

    updated = storage.update_reservation(reservation_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Reservation not found")

    if update_data.get("status") == "cancelled":
        resource = storage.get_resource_by_id(reservation["resource_id"])
        if resource and not resource.get("available"):
            storage.update_resource(
                reservation["resource_id"],
                {"available": True, "reserved_by": None},
            )

    return _build_reservation_summary(storage.get_reservation_by_id(reservation_id))


@router.delete("/reservations/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reservation(
    reservation_id: int,
    admin_user: Dict[str, Any] = Depends(require_admin),
) -> None:
    """Delete reservation (admin only)."""
    if not storage.delete_reservation(reservation_id):
        raise HTTPException(status_code=404, detail="Reservation not found")
