from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db_models import DeviceCommand


def queue_command(
    db: Session,
    *,
    device_id: int,
    action: str,
    payload: Optional[Dict[str, Any]] = None,
) -> DeviceCommand:
    """Create and persist a new device command."""

    command = DeviceCommand(device_id=device_id, action=action, payload=payload)
    db.add(command)
    db.flush()
    return command


def fetch_next_command(db: Session, device_id: int) -> Optional[DeviceCommand]:
    """Retrieve the next pending command for a device and mark it consumed."""

    command = db.scalar(
        select(DeviceCommand)
        .where(DeviceCommand.device_id == device_id)
        .where(DeviceCommand.consumed_at.is_(None))
        .order_by(DeviceCommand.created_at)
        .limit(1)
    )
    if not command:
        return None

    command.consumed_at = datetime.utcnow()
    db.flush()
    return command
