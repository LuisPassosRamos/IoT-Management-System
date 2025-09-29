from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.db_models import AuditLog
from app.models.schemas import AuditLogEntry
from app.services.auth import require_admin

router = APIRouter()


@router.get("/audit-logs", response_model=List[AuditLogEntry])
async def list_audit_logs(
    admin_user=Depends(require_admin),
    db: Session = Depends(get_db),
) -> List[AuditLogEntry]:
    logs = db.scalars(
        select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(500)
    ).all()
    return [
        AuditLogEntry(
            id=log.id,
            timestamp=log.timestamp,
            user_id=log.user_id,
            action=log.action,
            resource_id=log.resource_id,
            device_id=log.device_id,
            reservation_id=log.reservation_id,
            result=log.result,
            details=log.details,
        )
        for log in logs
    ]
