from __future__ import annotations

import csv
from datetime import datetime
from io import StringIO, BytesIO
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.db_models import (
    Reservation,
    ReservationStatus,
    Resource,
    User,
    UserRole,
)
from app.models.schemas import (
    ReservationResponse,
    ReservationFilter,
    StatsResponse,
    StatsReservationSummary,
    ResourceUsageEntry,
)
from app.services.auth import require_active_user, require_admin

router = APIRouter()


def _serialize_reservation(reservation: Reservation) -> ReservationResponse:
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
        resource_name=reservation.resource.name if reservation.resource else None,
        username=reservation.user.username if reservation.user else None,
    )


def _apply_filters(query, filters: ReservationFilter) -> None:
    if filters.resource_id is not None:
        query = query.where(Reservation.resource_id == filters.resource_id)
    if filters.user_id is not None:
        query = query.where(Reservation.user_id == filters.user_id)
    if filters.status is not None:
        query = query.where(Reservation.status == ReservationStatus(filters.status))
    if filters.start_from is not None:
        query = query.where(Reservation.start_time >= filters.start_from)
    if filters.start_to is not None:
        query = query.where(Reservation.start_time <= filters.start_to)
    return query


@router.get("/reservations/export")
async def export_reservations(
    format: str = "csv",
    filters: ReservationFilter = Depends(),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Response:
    """Export reservations to CSV or PDF (admin only)."""

    reservations = await list_reservations(filters, admin_user, db)

    if format == "csv":
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "ID",
                "Resource",
                "User",
                "Start",
                "End",
                "Expires",
                "Status",
                "Notes",
            ]
        )
        for item in reservations:
            writer.writerow(
                [
                    item.id,
                    item.resource_name,
                    item.username,
                    item.start_time.isoformat(),
                    item.end_time.isoformat() if item.end_time else "",
                    item.expires_at.isoformat(),
                    item.status,
                    item.notes or "",
                ]
            )
        buffer.seek(0)
        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=reservations.csv"
            },
        )

    if format == "pdf":
        try:
            from fpdf import FPDF
        except ImportError as exc:
            raise HTTPException(status_code=500, detail="PDF export not available") from exc

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Historico de Reservas", ln=True, align="C")
        pdf.ln(5)
        pdf.set_font("Arial", size=10)
        for item in reservations:
            pdf.multi_cell(
                0,
                7,
                txt=(
                    f"ID: {item.id} | Resource: {item.resource_name} | User: {item.username}\n"
                    f"Inicio: {item.start_time.isoformat()} | Fim: {item.end_time.isoformat() if item.end_time else '-'} | Status: {item.status}\n"
                ),
                border=1,
            )
            pdf.ln(2)
        pdf_buffer = BytesIO()
        pdf.output(pdf_buffer)
        pdf_buffer.seek(0)
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=reservations.pdf"
            },
        )

    raise HTTPException(status_code=400, detail="Unsupported export format")


@router.get("/reservations", response_model=List[ReservationResponse])
async def list_reservations(
    filters: ReservationFilter = Depends(),
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db),
) -> List[ReservationResponse]:
    """List reservations filtered by query parameters."""

    query = (
        select(Reservation)
        .options(
            selectinload(Reservation.resource),
            selectinload(Reservation.user),
        )
        .order_by(Reservation.start_time.desc())
    )
    query = _apply_filters(query, filters)

    if current_user.role != UserRole.ADMIN:
        permitted_ids = {perm.resource_id for perm in current_user.permissions}
        query = query.where(
            (Reservation.user_id == current_user.id)
            | Reservation.resource_id.in_(permitted_ids)
        )

    reservations = db.scalars(query).unique().all()
    return [_serialize_reservation(reservation) for reservation in reservations]


@router.get("/reservations/{reservation_id}", response_model=ReservationResponse)
async def get_reservation(
    reservation_id: int,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db),
) -> ReservationResponse:
    """Get a reservation by ID."""

    reservation = db.scalar(
        select(Reservation)
        .options(
            selectinload(Reservation.resource),
            selectinload(Reservation.user),
        )
        .where(Reservation.id == reservation_id)
    )
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    if current_user.role != UserRole.ADMIN:
        permitted_ids = {perm.resource_id for perm in current_user.permissions}
        if (
            reservation.user_id != current_user.id
            and reservation.resource_id not in permitted_ids
        ):
            raise HTTPException(status_code=403, detail="Access denied")

    return _serialize_reservation(reservation)


@router.get("/reservations/stats/summary", response_model=StatsResponse)
async def reservation_stats(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> StatsResponse:
    """Return reservation statistics for dashboard usage."""

    total_res = db.scalar(select(func.count()).select_from(Reservation)) or 0
    active_res = db.scalar(
        select(func.count())
        .select_from(Reservation)
        .where(Reservation.status == ReservationStatus.ACTIVE)
    ) or 0
    avg_duration = db.scalar(
        select(func.avg(func.julianday(Reservation.end_time) - func.julianday(Reservation.start_time)))
        .where(Reservation.end_time.is_not(None))
    )
    avg_minutes = float(avg_duration * 24 * 60) if avg_duration else 0.0

    top_resources_rows = db.execute(
        select(
            Reservation.resource_id,
            Resource.name,
            func.count(Reservation.id),
            func.sum(
                (func.julianday(Reservation.end_time) - func.julianday(Reservation.start_time))
                * 24
                * 60
            ),
        )
        .join(Resource, Resource.id == Reservation.resource_id)
        .where(Reservation.end_time.is_not(None))
        .group_by(Reservation.resource_id, Resource.name)
        .order_by(func.count(Reservation.id).desc())
        .limit(5)
    ).all()

    top_resources = [
        ResourceUsageEntry(
            resource_id=row[0],
            resource_name=row[1],
            total_reservations=row[2],
            total_minutes=float(row[3]) if row[3] else 0.0,
        )
        for row in top_resources_rows
    ]

    usage_rows = db.execute(
        select(
            func.strftime("%Y-%m-%d", Reservation.start_time),
            func.count(Reservation.id),
        )
        .group_by(func.strftime("%Y-%m-%d", Reservation.start_time))
        .order_by(func.strftime("%Y-%m-%d", Reservation.start_time))
    ).all()

    usage_by_day = {row[0]: row[1] for row in usage_rows}

    summary = StatsReservationSummary(
        total_reservations=total_res,
        active_reservations=active_res,
        average_duration_minutes=round(avg_minutes, 2),
    )

    return StatsResponse(
        reservations=summary,
        top_resources=top_resources,
        usage_by_day=usage_by_day,
    )
