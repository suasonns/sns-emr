"""
Backwards compatible shim.

Canonical get_db lives in app.core.database.
"""

from app.core.database import get_db  # noqa: F401