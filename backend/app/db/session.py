"""
Compatibility wrapper.

This project defines the canonical DB session in app.core.database / app.core.db.
Import SessionLocal from there so old imports don't break.
"""

from app.core.db import SessionLocal  # noqa: F401