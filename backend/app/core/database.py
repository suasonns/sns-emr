"""
Enterprise-grade database core for SNS Hospice EMR.
"""

from __future__ import annotations

# -----------------------------------------------------
# Environment loading
# -----------------------------------------------------

from dotenv import load_dotenv

load_dotenv(".env.local")
load_dotenv()

# -----------------------------------------------------
# Imports
# -----------------------------------------------------

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# -----------------------------------------------------
# Canonical Base
# -----------------------------------------------------

from app.db.base import Base

# -----------------------------------------------------
# Database URL
# -----------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Refusing to start without explicit DB configuration."
    )

# -----------------------------------------------------
# Engine
# -----------------------------------------------------

engine = create_engine(
    DATABASE_URL,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args={"options": "-csearch_path=public"},
)

# -----------------------------------------------------
# Session
# -----------------------------------------------------

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

# -----------------------------------------------------
# ✅ DEV TENANT MODE
# -----------------------------------------------------
# IMPORTANT:
# None = SUPER ADMIN MODE (ACCESS ALL TENANTS)
# UUID = SINGLE TENANT MODE (RESTRICTED)

DEV_TENANT_ID = None

# -----------------------------------------------------
# DB Dependency
# -----------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """
    ENTERPRISE BEHAVIOR:

    DEV MODE:
    - tenant_id = None → ALL tenants accessible (SUPER ADMIN)

    PRODUCTION:
    - tenant_id must come from JWT / auth layer
    - NEVER leave as None in production

    This value is injected into SQLAlchemy session.info
    and consumed by tenant_orm_filters.
    """

    db = SessionLocal()

    # ✅ CRITICAL: Tenant injection
    db.info["tenant_id"] = DEV_TENANT_ID

    try:
        yield db
    finally:
        db.close()