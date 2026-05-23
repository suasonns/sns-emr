"""
Enterprise-grade database core for SNS Hospice EMR.

This module intentionally provides:
- engine
- SessionLocal
- Base
- get_db (FastAPI dependency)
- Optional tenant RLS hook

CRITICAL GUARANTEE:
- Environment variables are loaded BEFORE engine creation
"""

from __future__ import annotations

# ---------------------------------------------------------------------
# Environment loading (MUST be first)
# ---------------------------------------------------------------------
from dotenv import load_dotenv

# Explicit local override first, then fallback
load_dotenv(".env.local")
load_dotenv()

import os
from typing import Generator, Optional

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# ---------------------------------------------------------------------
# Database URL (ENV is authoritative; fallback is DEV-ONLY safety net)
# ---------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Refusing to start without explicit DB configuration."
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
# FastAPI DB dependency (canonical)
# ---------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------------------
# Optional: Tenant context hook (RLS-ready, safe no-op if unused)
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