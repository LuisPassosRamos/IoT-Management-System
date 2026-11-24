import atexit
import os
from pathlib import Path
from tempfile import TemporaryDirectory


# App modules configure their engine at import time, before fixtures run.
_database_dir = TemporaryDirectory()
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_database_dir.name) / 'iot.sqlite3'}"


@atexit.register
def _clean_database():
    from app.db.session import engine

    engine.dispose()
    _database_dir.cleanup()
