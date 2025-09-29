from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.db_models import AuditLog

settings = get_settings()


def record_audit(
    db: Session,
    *,
    action: str,
    user_id: Optional[int] = None,
    resource_id: Optional[int] = None,
    device_id: Optional[int] = None,
    reservation_id: Optional[int] = None,
    result: str = "success",
    details: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """Persist an audit log entry."""

    entry = AuditLog(
        action=action,
        user_id=user_id,
        resource_id=resource_id,
        device_id=device_id,
        reservation_id=reservation_id,
        result=result,
        details=details,
    )
    db.add(entry)
    db.flush()
    return entry


def purge_old_logs(db: Session) -> int:
    """Delete logs older than retention period."""

    cutoff = datetime.utcnow() - timedelta(days=settings.audit_log_retention_days)
    old_logs = db.scalars(select(AuditLog).where(AuditLog.timestamp < cutoff)).all()
    deleted = len(old_logs)
    for log in old_logs:
        db.delete(log)
    return deleted
