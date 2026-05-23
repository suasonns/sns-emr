"""
Enterprise-grade database core for SNS Hospice EMR.

This module intentionally provides:
- engine
- SessionLocal
- Base
- get_db (FastAPI dependency) for backwards compatibility with existing app.api modules
"""

from __future__ import annotations

import os
from typing import Generator, Optional

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# ---------------------------------------------------------------------
# Database URL (ENV first, safe fallback for local DEV only)
# ---------------------------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://sns_user:sns_password@127.0.0.1:5433/sns_emr",
)

# ---------------------------------------------------------------------
# SQLAlchemy Engine (enterprise-safe defaults)
# ---------------------------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args={"options": "-csearch_path=public"},
)

# ---------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

# ---------------------------------------------------------------------
# Declarative Base (SINGLE SOURCE OF TRUTH)
# ---------------------------------------------------------------------
Base = declarative_base()

# ---------------------------------------------------------------------
# Backwards-compatible FastAPI dependency (used by existing app.api modules)
# ---------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------------------
# Optional: Tenant context hook (RLS-ready)
# ---------------------------------------------------------------------
_CURRENT_TENANT: Optional[str] = None


def set_current_tenant(tenant_id: Optional[str]) -> None:
    global _CURRENT_TENANT
    _CURRENT_TENANT = tenant_id


def get_current_tenant() -> Optional[str]:
    return _CURRENT_TENANT


@event.listens_for(Session, "after_begin")
def _set_rls_tenant(session: Session, transaction, connection) -> None:
    tenant_id = get_current_tenant()
    if tenant_id:
        connection.execute(
            text("SET LOCAL app.current_tenant = :tenant_id"),
            {"tenant_id": tenant_id},
        )