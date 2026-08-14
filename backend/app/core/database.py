"""
Enterprise-grade database core for SNS Hospice EMR.
"""

from __future__ import annotations

# -----------------------------------------------------
# Environment loading (CANONICAL)
# -----------------------------------------------------

from dotenv import load_dotenv

load_dotenv(".env.local")
load_dotenv()

# -----------------------------------------------------
# Imports
# -----------------------------------------------------

import os
import re
from typing import Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.db.base import Base  # noqa: F401  (import anchor)

# -----------------------------------------------------
# Database URL (REQUIRED)
# -----------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Refusing to start without explicit DB configuration."
    )

# -----------------------------------------------------
# Phase 3 Feature Flag — TENANT ROUTING (default OFF)
# -----------------------------------------------------

TENANT_ROUTING_ENABLED = (
    os.getenv("TENANT_ROUTING_ENABLED", "false").lower() == "true"
)

# -----------------------------------------------------
# Engine
# -----------------------------------------------------
# Default search_path remains public. Tenant routing overrides per-request via SET LOCAL.
# -----------------------------------------------------

engine = create_engine(
    DATABASE_URL,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args={"options": "-csearch_path=public -c TimeZone=UTC"},
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

# -----------------------------------------------------
# STARTUP SAFETY CHECKS (ENTERPRISE GUARDRAIL)
# -----------------------------------------------------

def _verify_expected_database(_engine) -> None:
    """
    Verifies the app is connected to the expected DB/user/host/port.
    Normalizes inet_server_addr() which may return CIDR (e.g., 127.0.0.1/32).
    If EXPECTED_* variables are not set, this check is skipped.
    """
    expected_db = os.getenv("EXPECTED_DB")
    expected_user = os.getenv("EXPECTED_DB_USER")
    expected_host = os.getenv("EXPECTED_DB_HOST")
    expected_port = os.getenv("EXPECTED_DB_PORT")

    # If not all are present, skip (explicit choice)
    if not all([expected_db, expected_user, expected_host, expected_port]):
        return

    with _engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT
                    current_database() AS db,
                    current_user AS user,
                    inet_server_addr()::text AS host,
                    inet_server_port()::text AS port
                """
            )
        ).mappings().one()

    # ✅ Normalize CIDR host (e.g., 127.0.0.1/32 -> 127.0.0.1)
    actual_host = (row["host"] or "").split("/")[0]
    actual_port = row["port"]

    if (
        row["db"] != expected_db
        or row["user"] != expected_user
        or actual_host != expected_host
        or actual_port != expected_port
    ):
        raise RuntimeError(
            "DATABASE SAFETY CHECK FAILED:\n"
            f"  Connected: db={row['db']}, user={row['user']}, host={row['host']}, port={row['port']}\n"
            f"  Expected : db={expected_db}, user={expected_user}, host={expected_host}, port={expected_port}\n"
            "Refusing to start."
        )


_verify_expected_database(engine)

# -----------------------------------------------------
# Internal helpers (enterprise-safe)
# -----------------------------------------------------

_SCHEMA_RE = re.compile(r"^[a-z_][a-z0-9_]*$")  # keep schema names lowercase/underscore


def _safe_schema(schema_name: Optional[str]) -> Optional[str]:
    """
    Validate schema name to prevent injection.
    Allow only [a-z0-9_] and must start with letter/_ (lowercase only).
    """
    if not schema_name:
        return None
    schema_name = schema_name.strip()
    if not schema_name:
        return None
    if not _SCHEMA_RE.match(schema_name):
        return None
    return schema_name


def _apply_search_path(db: Session, schema_name: Optional[str]) -> None:
    """
    Apply request-scoped search_path.
    Always includes public as fallback when tenant routing is enabled.
    """
    schema_name = _safe_schema(schema_name)

    if TENANT_ROUTING_ENABLED and schema_name:
        # schema_name is validated (lowercase/underscore), so this is safe.
        db.execute(text(f"SET LOCAL search_path = {schema_name}, public"))
    else:
        db.execute(text("SET LOCAL search_path = public"))


def get_db() -> Generator[Session, None, None]:
    """
    Standard DB session dependency.

    Enterprise routing behavior:
    - Default is public (unchanged)
    - If TENANT_ROUTING_ENABLED and request context has a tenant schema,
      apply SET LOCAL search_path = tenant_schema, public
    """
    from app.core.tenant_schema_context import get_current_tenant_schema  # local import avoids cycles

    db = SessionLocal()
    try:
        _apply_search_path(db, get_current_tenant_schema())
        yield db
    finally:
        db.close()