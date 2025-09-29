from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, Tuple, List

from fastapi import HTTPException, status
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.db_models import (
    Resource,
    ResourceStatus,
    Reservation,
    ReservationStatus,
    User,
    UserRole,
)
from app.services import audit
from app.services.notifications import manager as notification_manager

settings = get_settings()


def _compute_expires_at(start_time: datetime, duration_minutes: int) -> datetime:
    return start_time + timedelta(minutes=duration_minutes)


def ensure_user_can_manage_resource(user: User, resource: Resource) -> None:
    """Ensure the user has permission over the resource."""

    if user.role == UserRole.ADMIN:
        return

    permitted_ids = {perm.resource_id for perm in user.permissions}
    if resource.id not in permitted_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have permission for this resource",
        )


def get_active_reservation(db: Session, resource_id: int) -> Optional[Reservation]:
    """Return active reservation for a resource if it exists."""

    return db.scalar(
        select(Reservation)
        .where(Reservation.resource_id == resource_id)
        .where(Reservation.status == ReservationStatus.ACTIVE)
        .order_by(Reservation.start_time.desc())
    )


def ensure_no_conflict(
    db: Session,
    *,
    resource: Resource,
    start_time: datetime,
    end_time: datetime,
) -> None:
    """Ensure no reservation overlaps the given window."""

    conflict = db.scalar(
        select(Reservation)
        .where(Reservation.resource_id == resource.id)
        .where(
            Reservation.status.in_(
                [
                    ReservationStatus.ACTIVE,
                    ReservationStatus.SCHEDULED,
                ]
            )
        )
        .where(
            or_(
                and_(Reservation.start_time <= start_time, Reservation.expires_at > start_time),
                and_(Reservation.start_time < end_time, Reservation.expires_at >= end_time),
                and_(Reservation.start_time >= start_time, Reservation.expires_at <= end_time),
            )
        )
    )

    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resource already reserved in the selected period",
        )


def create_reservation(
    db: Session,
    *,
    resource: Resource,
    user: User,
    duration_minutes: int,
    start_time: Optional[datetime] = None,
    notes: Optional[str] = None,
) -> Reservation:
    """Create a reservation ensuring conflicts are avoided."""

    now = datetime.utcnow()
    start = start_time or now
    if start < now - timedelta(minutes=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start time must be in the future or near present",
        )

    expires_at = _compute_expires_at(start, duration_minutes)

    ensure_user_can_manage_resource(user, resource)
    ensure_no_conflict(db, resource=resource, start_time=start, end_time=expires_at)

    reservation_status = (
        ReservationStatus.SCHEDULED if start > now + timedelta(minutes=1) else ReservationStatus.ACTIVE
    )

    reservation = Reservation(
        resource_id=resource.id,
        user_id=user.id,
        start_time=start,
        expires_at=expires_at,
        status=reservation_status,
        notes=notes,
    )
    db.add(reservation)
    db.flush()

    if reservation.status == ReservationStatus.ACTIVE:
        resource.status = ResourceStatus.RESERVED

    audit.record_audit(
        db,
        action="reservation_created",
        user_id=user.id,
        resource_id=resource.id,
        reservation_id=reservation.id,
        details={"duration_minutes": duration_minutes},
    )

    notification_manager.schedule_broadcast(
        {
            "type": "reservation.created",
            "reservationId": reservation.id,
            "resourceId": resource.id,
            "userId": user.id,
            "status": reservation.status.value,
        }
    )
    notification_manager.schedule_broadcast(
        {
            "type": "resource.updated",
            "resourceId": resource.id,
            "status": resource.status.value,
        }
    )

    return reservation


def activate_scheduled_reservations(db: Session) -> List[int]:
    """Activate reservations whose start time has arrived."""

    now = datetime.utcnow()
    reservations = db.scalars(
        select(Reservation)
        .where(Reservation.status == ReservationStatus.SCHEDULED)
        .where(Reservation.start_time <= now)
    ).all()

    activated: List[int] = []
    for reservation in reservations:
        reservation.status = ReservationStatus.ACTIVE
        reservation.resource.status = ResourceStatus.RESERVED
        activated.append(reservation.id)
        audit.record_audit(
            db,
            action="reservation_activated",
            user_id=reservation.user_id,
            resource_id=reservation.resource_id,
            reservation_id=reservation.id,
        )
        notification_manager.schedule_broadcast(
            {
                "type": "reservation.updated",
                "reservationId": reservation.id,
                "resourceId": reservation.resource_id,
                "userId": reservation.user_id,
                "status": reservation.status.value,
            }
        )
        notification_manager.schedule_broadcast(
            {
                "type": "resource.updated",
                "resourceId": reservation.resource_id,
                "status": reservation.resource.status.value,
            }
        )
    return activated


def release_reservation(
    db: Session,
    *,
    reservation: Reservation,
    by_user: User,
    notes: Optional[str] = None,
    force: bool = False,
) -> Reservation:
    """Release an active reservation."""

    if reservation.status not in {ReservationStatus.ACTIVE, ReservationStatus.SCHEDULED}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reservation already closed",
        )

    if reservation.status == ReservationStatus.SCHEDULED:
        reservation.status = ReservationStatus.CANCELLED
    else:
        if reservation.user_id != by_user.id and by_user.role != UserRole.ADMIN and not force:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only release your own reservations",
            )
        reservation.status = ReservationStatus.COMPLETED
        reservation.end_time = datetime.utcnow()

    reservation.notes = notes or reservation.notes
    if by_user.role == UserRole.ADMIN and reservation.user_id != by_user.id:
        reservation.released_by_admin = True

    resource = reservation.resource
    has_other_active = db.scalar(
        select(Reservation)
        .where(Reservation.resource_id == resource.id)
        .where(Reservation.status == ReservationStatus.ACTIVE)
        .where(Reservation.id != reservation.id)
    )
    if not has_other_active:
        resource.status = ResourceStatus.AVAILABLE

    audit.record_audit(
        db,
        action="reservation_released",
        user_id=by_user.id,
        resource_id=reservation.resource_id,
        reservation_id=reservation.id,
        details={"forced": force},
    )

    notification_manager.schedule_broadcast(
        {
            "type": "reservation.updated",
            "reservationId": reservation.id,
            "resourceId": reservation.resource_id,
            "userId": reservation.user_id,
            "status": reservation.status.value,
        }
    )
    notification_manager.schedule_broadcast(
        {
            "type": "resource.updated",
            "resourceId": reservation.resource_id,
            "status": reservation.resource.status.value,
        }
    )

    return reservation


def expire_overdue_reservations(db: Session) -> List[int]:
    """Expire reservations that exceeded timeout."""

    now = datetime.utcnow()
    overdue = db.scalars(
        select(Reservation)
        .where(Reservation.status == ReservationStatus.ACTIVE)
        .where(Reservation.expires_at <= now)
    ).all()

    expired_ids: List[int] = []
    for reservation in overdue:
        reservation.status = ReservationStatus.EXPIRED
        reservation.end_time = reservation.expires_at
        reservation.resource.status = ResourceStatus.AVAILABLE
        expired_ids.append(reservation.id)
        audit.record_audit(
            db,
            action="reservation_expired",
            user_id=reservation.user_id,
            resource_id=reservation.resource_id,
            reservation_id=reservation.id,
            details={"expired_at": reservation.expires_at.isoformat()},
        )
        notification_manager.schedule_broadcast(
            {
                "type": "reservation.updated",
                "reservationId": reservation.id,
                "resourceId": reservation.resource_id,
                "userId": reservation.user_id,
                "status": reservation.status.value,
            }
        )
        notification_manager.schedule_broadcast(
            {
                "type": "resource.updated",
                "resourceId": reservation.resource_id,
                "status": reservation.resource.status.value,
            }
        )
    return expired_ids
