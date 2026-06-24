from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# ---------------------------------------------------------
# ✅ ENTERPRISE NAMING CONVENTION (NON-NEGOTIABLE)
# ---------------------------------------------------------

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


# ---------------------------------------------------------
# ✅ CANONICAL BASE (USED BY ALL MODELS)
# ---------------------------------------------------------

class Base(DeclarativeBase):
    """
    ✅ Canonical SQLAlchemy Base for SNS Hospice EMR

    CRITICAL RULES:
    - ALL ORM models must inherit from this Base
    - Alembic uses this metadata for autogenerate
    - No model should define its own metadata
    """
    metadata = metadata


# ---------------------------------------------------------
# 🔴 CRITICAL: FORCE MODEL REGISTRATION
# ---------------------------------------------------------
# ✅ This guarantees all models are loaded into SQLAlchemy metadata
# ✅ Required for Alembic autogenerate to detect tables

import app.models  # noqa: F401