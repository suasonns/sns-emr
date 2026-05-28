"""
Enterprise-grade DB facade (single import contract).

Why this exists:
- Prevents session/import drift across the service layer
- Provides a stable import path for SessionLocal and get_db
- Allows older service modules to keep working while refactoring

IMPORTANT RULES (NON-NEGOTIABLE):
- MODELS must import Base / BaseModel from app.db.base or app.models.base
- SERVICES / ROUTERS may import get_db from this module
- This module MUST NOT be used as a Base import by ORM models
"""

from typing import Generator
from sqlalchemy.orm import Session

# Canonical DB objects (re-exported for services only)
from app.core.database import SessionLocal
from app.db.base import Base  # exposed for typing/debug only, NOT model inheritance


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency: yields a DB session and always closes it.

    ⚠️ For NON-TENANT access only.
    Tenant-scoped access must use get_db_tenant.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
