from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# ---------------------------------------------------------
# FULL NAMING CONVENTION (ENTERPRISE REQUIRED)
# ---------------------------------------------------------

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    """
    ✅ Canonical SQLAlchemy Base for SNS Hospice EMR

    CRITICAL RULES:
    - ALL models must inherit from this Base
    - Alembic uses this metadata for autogenerate
    """
    metadata = metadata


# ---------------------------------------------------------
# 🔴 CRITICAL: MODEL REGISTRATION (NEVER REMOVE)
# ---------------------------------------------------------

# This MUST run at import time so Alembic sees all tables

import app.models  # noqa: F401
