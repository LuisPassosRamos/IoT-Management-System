from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.db_models import (
    Device,
    Resource,
    ResourceStatus,
    Reservation,
    ReservationStatus,
    User,
    UserRole,
)
from app.models.schemas import (
    ResourceCreate,
    ResourceUpdate,
    ResourceResponse,
    ReservationCreate,
    ReservationRelease,
    ReservationResponse,
)
from app.services.auth import require_active_user, require_admin
from app.services import reservation_service, audit
from app.services.notifications import manager as notification_manager

router = APIRouter()


def _serialize_device(device: Device | None) -> dict | None:
    if not device:
        return None
    return {
        "id": device.id,
        "name": device.name,
        "type": device.type.value,
        "status": device.status,
        "resource_id": device.resource_id,
        "numeric_value": device.numeric_value,
        "text_value": device.text_value,
        "metadata": device.metadata_json,
        "last_reported_at": device.last_reported_at,
    }


def _serialize_reservation(reservation: Reservation) -> ReservationResponse:
    resource = reservation.resource
    user = reservation.user
    return ReservationResponse(
        id=reservation.id,
        resource_id=reservation.resource_id,
        user_id=reservation.user_id,
        start_time=reservation.start_time,
        end_time=reservation.end_time,
        expires_at=reservation.expires_at,
        status=reservation.status.value,
        notes=reservation.notes,
        released_by_admin=reservation.released_by_admin,
        resource_name=resource.name if resource else None,
        username=user.username if user else None,
    )


def _serialize_resource(resource: Resource) -> ResourceResponse:
    active_reservation = next(
        (res for res in resource.reservations if res.status == ReservationStatus.ACTIVE),
        None,
    )
    return ResourceResponse(
        id=resource.id,
        name=resource.name,
        description=resource.description,
        type=resource.type,
        location=resource.location,
        capacity=resource.capacity,
        status=resource.status.value,
        current_reservation_id=active_reservation.id if active_reservation else None,
        reserved_by_user=
        active_reservation.user.username if active_reservation and active_reservation.user else None,
        device=_serialize_device(resource.device),
    )


@router.get("/resources", response_model=List[ResourceResponse])
async def list_resources(
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db),
) -> List[ResourceResponse]:
    """List resources filtered by user permissions."""

    query = (
        select(Resource)
        .options(
            selectinload(Resource.device),
            selectinload(Resource.reservations).selectinload(Reservation.user),
        )
        .order_by(Resource.name)
    )

    if current_user.role != UserRole.ADMIN:
        permitted_ids = [perm.resource_id for perm in current_user.permissions]
        if not permitted_ids:
            return []
        query = query.where(Resource.id.in_(permitted_ids))

    resources = db.scalars(query).unique().all()
    return [_serialize_resource(resource) for resource in resources]


@router.get("/resources/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: int,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db),
) -> ResourceResponse:
    """Get a single resource."""

    resource = db.scalar(
        select(Resource)
        .options(
            selectinload(Resource.device),
            selectinload(Resource.reservations).selectinload(Reservation.user),
        )
        .where(Resource.id == resource_id)
    )
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    reservation_service.ensure_user_can_manage_resource(current_user, resource)
    return _serialize_resource(resource)


@router.post("/resources", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    payload: ResourceCreate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ResourceResponse:
    """Create a new resource (admin only)."""

    try:
        status_value = (
            ResourceStatus(payload.status)
            if payload.status
            else ResourceStatus.AVAILABLE
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid resource status") from exc

    resource = Resource(
        name=payload.name,
        description=payload.description,
        type=payload.type,
        location=payload.location,
        capacity=payload.capacity,
        status=status_value,
    )
    db.add(resource)
    db.flush()

    if payload.device_id is not None:
        device = db.get(Device, payload.device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        device.resource_id = resource.id

    audit.record_audit(
        db,
        action="resource_created",
        user_id=admin_user.id,
        resource_id=resource.id,
        details={"device_id": payload.device_id},
    )
    notification_manager.schedule_broadcast(
        {
            "type": "resource.created",
            "resourceId": resource.id,
            "status": resource.status.value,
        }
    )

    return _serialize_resource(resource)


@router.put("/resources/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_id: int,
    payload: ResourceUpdate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ResourceResponse:
    """Update resource information (admin only)."""

    resource = db.scalar(
        select(Resource)
        .options(
            selectinload(Resource.device),
            selectinload(Resource.reservations).selectinload(Reservation.user),
        )
        .where(Resource.id == resource_id)
    )
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    updates = payload.model_dump(exclude_unset=True)
    if "status" in updates and updates["status"] is not None:
        try:
            resource.status = ResourceStatus(updates.pop("status"))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid resource status") from exc

    if "device_id" in updates:
        device_id = updates.pop("device_id")
        if device_id is None and resource.device:
            resource.device.resource_id = None
        elif device_id is not None:
            device = db.get(Device, device_id)
            if not device:
                raise HTTPException(status_code=404, detail="Device not found")
            device.resource_id = resource.id

    for attr, value in updates.items():
        setattr(resource, attr, value)

    audit.record_audit(
        db,
        action="resource_updated",
        user_id=admin_user.id,
        resource_id=resource.id,
        details=payload.model_dump(exclude_unset=True),
    )
    notification_manager.schedule_broadcast(
        {
            "type": "resource.updated",
            "resourceId": resource.id,
            "status": resource.status.value,
        }
    )

    db.flush()
    return _serialize_resource(resource)


@router.delete("/resources/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(
    resource_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    """Delete a resource (admin only)."""

    resource = db.get(Resource, resource_id)
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    if resource.device:
        resource.device.resource_id = None

    audit.record_audit(
        db,
        action="resource_deleted",
        user_id=admin_user.id,
        resource_id=resource.id,
    )
    notification_manager.schedule_broadcast(
        {
            "type": "resource.deleted",
            "resourceId": resource.id,
        }
    )

    db.delete(resource)


@router.post("/resources/{resource_id}/reserve", response_model=ReservationResponse)
async def reserve_resource(
    resource_id: int,
    payload: ReservationCreate,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db),
) -> ReservationResponse:
    """Create a reservation for a resource."""

    resource = db.scalar(
        select(Resource)
        .options(selectinload(Resource.reservations).selectinload(Reservation.user))
        .where(Resource.id == resource_id)
    )
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    target_user = current_user
    if current_user.role == UserRole.ADMIN and payload.user_id:
        target_user = db.get(User, payload.user_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="Target user not found")

    reservation = reservation_service.create_reservation(
        db,
        resource=resource,
        user=target_user,
        duration_minutes=payload.duration_minutes,
        start_time=payload.start_time,
        notes=payload.notes,
    )

    db.flush()
    db.refresh(reservation)
    return _serialize_reservation(reservation)


@router.post("/resources/{resource_id}/release", response_model=ReservationResponse)
async def release_resource(
    resource_id: int,
    payload: ReservationRelease,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db),
) -> ReservationResponse:
    """Release the active reservation for a resource."""

    reservation = reservation_service.get_active_reservation(db, resource_id)
    if not reservation:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resource is not reserved")

    if payload.force and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can force release")

    updated = reservation_service.release_reservation(
        db,
        reservation=reservation,
        by_user=current_user,
        notes=payload.notes,
        force=payload.force,
    )

    db.flush()
    db.refresh(updated)
    return _serialize_reservation(updated)
