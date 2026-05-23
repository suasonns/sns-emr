"""
Enterprise-grade DB facade (single import contract).

Why this exists:
- Prevents schema/import drift across the codebase
- Provides a stable import path for Base, SessionLocal, and get_db
- Allows older modules to keep working while you refactor gradually

Canonical usage:
- Models: from app.core.db import Base
- Routers/services: from app.core.db import get_db
"""

from typing import Generator
from sqlalchemy.orm import Session

from app.core.database import Base, SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency: yields a DB session and always closes it.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
