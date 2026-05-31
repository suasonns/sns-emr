"""
Enterprise DB facade (stable import layer).
"""

from typing import Generator
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.db.base import Base  # for typing/debug only!


def get_db() -> Generator[Session, None, None]:
    """
    Standard DB session dependency
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
