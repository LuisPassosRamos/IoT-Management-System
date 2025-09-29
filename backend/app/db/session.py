from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator, Dict, Any

from app.core.config import get_settings

settings = get_settings()


def _ensure_sqlite_dir(url: str) -> None:
    """Create SQLite directory if needed."""

    if url.startswith("sqlite"):
        path = url.split("sqlite:///")[-1]
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)


def _get_sqlite_connect_args(url: str) -> Dict[str, Any]:
    """Return SQLite-specific connection arguments."""

    if url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


_ensure_sqlite_dir(settings.database_url)

engine = create_engine(
    settings.database_url,
    connect_args=_get_sqlite_connect_args(settings.database_url),
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def get_db() -> Generator:
    """Provide a transactional scope around a series of operations."""

    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
