from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# ---------------------------------------------------------
# Canonical SQLAlchemy metadata with deterministic naming
# ---------------------------------------------------------
# This naming convention is REQUIRED for:
# - Alembic autogenerate stability
# - Forward-only migrations
# - Survey-defensible schema evolution
# ---------------------------------------------------------

NAMING_CONVENTION = {
    # Indexes
    "ix": "ix_%(table_name)s_%(column_0_name)s",

    # Unique constraints
    "uq": "uq_%(table_name)s_%(column_0_name)s",

    # Check constraints
    "ck": "ck_%(table_name)s_%(constraint_name)s",

    # Foreign keys
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",

    # Primary keys
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    """
    Canonical SQLAlchemy Base for SNS Hospice EMR.

    ✅ EXACTLY ONE Base in the entire codebase
    ✅ ALL ORM models MUST inherit from this Base
    ✅ Alembic autogenerate relies on this metadata
    ✅ Forward-only schema evolution
    ✅ Enterprise / compliance safe
    """
    metadata = metadata


# ---------------------------------------------------------
# CRITICAL: import models so tables register with metadata
# ---------------------------------------------------------
# This MUST execute at import time.
#
# If this import is removed:
# - Base.metadata.tables will be empty
# - Alembic autogenerate will propose DROP TABLE migrations
#
# app.models MUST import all ORM models (User, Patient, Task, Visit, etc.)
# ---------------------------------------------------------
import app.models  # noqa: F401