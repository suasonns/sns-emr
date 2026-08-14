from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _sync_database_url() -> str:
    """
    Build a psycopg2 sync URL for code paths that must not use asyncpg.
    """
    url = os.getenv("DATABASE_URL") or ""
    if not url:
        raise RuntimeError("DATABASE_URL must be set")

    # Force sync driver for psycopg2
    if "postgresql+asyncpg" in url:
        url = url.replace("postgresql+asyncpg", "postgresql+psycopg2")

    return url


# NOTE:
# Do NOT pass connect_args={"options": ...} here.
# asyncpg breaks on `options`, and we want a clean sync connection surface.
SYNC_ENGINE = create_engine(
    _sync_database_url(),
    future=True,
)

SyncSessionLocal = sessionmaker(
    bind=SYNC_ENGINE,
    autoflush=False,
    autocommit=False,
    future=True,
)