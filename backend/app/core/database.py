"""
Enterprise-grade database core for SNS Hospice EMR.

Provides:
- engine
- SessionLocal
- Base
- get_db
- NO global tenant state (tenant handled via get_db_tenant)
"""

from __future__ import annotations

# ---------------------------------------------------------------------
# Environment loading (MUST be first)
# ---------------------------------------------------------------------
from dotenv import load_dotenv

load_dotenv(".env.local")
load_dotenv()

# ---------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------
import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# ---------------------------------------------------------------------
# Database URL
# ---------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Refusing to start without explicit DB configuration."
    )

# ---------------------------------------------------------------------
# Engine
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
# Session
# ---------------------------------------------------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

# ---------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------
Base = declarative_base()

# ---------------------------------------------------------------------
# Default DB dependency (NON-TENANT)
# ---------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    """
    ⚠️ Use ONLY for non-tenant tables (tenants, system, admin)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()