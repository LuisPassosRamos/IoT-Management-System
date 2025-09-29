from __future__ import annotations

import asyncio
import logging
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.routers import auth, devices, resources, reservations, users, audit, realtime
from app.services import reservation_service, audit as audit_service

settings = get_settings()
logger = logging.getLogger("iot-management")
logger.setLevel(logging.INFO)

app = FastAPI(
    title=settings.app_name,
    description="Sistema de Gestao de Recursos Compartilhados com IoT",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, tags=["auth"])
app.include_router(users.router, tags=["users"])
app.include_router(resources.router, tags=["resources"])
app.include_router(devices.router, tags=["devices"])
app.include_router(reservations.router, tags=["reservations"])
app.include_router(audit.router, tags=["audit"])

_reservation_task: Optional[asyncio.Task] = None


async def _reservation_worker() -> None:
    """Background worker to process reservation lifecycle events."""

    interval = max(settings.reservation_check_interval_seconds, 15)
    while True:
        try:
            with SessionLocal() as db:
                activated = reservation_service.activate_scheduled_reservations(db)
                expired = reservation_service.expire_overdue_reservations(db)
                purged = audit_service.purge_old_logs(db)
                db.commit()
                if activated or expired:
                    logger.info(
                        "Reservation worker processed activated=%s expired=%s", activated, expired
                    )
                if purged:
                    logger.info("Purged %s audit logs", purged)
        except Exception as exc:  # pragma: no cover - background safety
            logger.exception("Reservation worker failure: %s", exc)
        await asyncio.sleep(interval)


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize database and background processes."""

    global _reservation_task
    init_db()
    if _reservation_task is None or _reservation_task.done():
        _reservation_task = asyncio.create_task(_reservation_worker())


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Gracefully stop background tasks."""

    global _reservation_task
    if _reservation_task:
        _reservation_task.cancel()
        try:
            await _reservation_task
        except asyncio.CancelledError:
            pass
        _reservation_task = None


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with API metadata."""

    return {
        "message": "IoT Management System API",
        "version": "2.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""

    return {"status": "healthy", "message": "API is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
