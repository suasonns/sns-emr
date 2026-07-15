from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger("sns_emr")


# =========================================================
# DATA MODEL
# =========================================================

@dataclass(frozen=True)
class TenantRecord:
    tenant_id: str
    schema_name: str   # kept for compatibility
    display_name: str
    status: str


# =========================================================
# CORE TENANT RESOLUTION (PRODUCTION SAFE)
# =========================================================

def get_tenant_by_id(db: Session, tenant_id: str) -> TenantRecord:
    """
    ✅ CANONICAL TENANT REGISTRY (ENTERPRISE SAFE)

    - Uses public.tenants as single source of truth
    - NO schema_name dependency (single schema model)
    - Enforces ACTIVE tenant lifecycle
    - Fail-safe rollback
    """

    try:
        stmt = text("""
            SELECT id, display_name, status
            FROM public.tenants
            WHERE id = :tenant_id
        """)

        row = db.execute(stmt, {"tenant_id": tenant_id}).fetchone()

        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"Tenant not found: {tenant_id}",
            )

        if row.status != "ACTIVE":
            raise HTTPException(
                status_code=403,
                detail=f"Tenant not active: {tenant_id}",
            )

        return TenantRecord(
            tenant_id=str(row.id),
            schema_name="public",  # ✅ FIXED: single schema model
            display_name=row.display_name,
            status=row.status,
        )

    except HTTPException:
        raise

    except Exception as exc:
        db.rollback()
        logger.exception(
            "Tenant lookup failed for tenant_id=%s",
            tenant_id,
        )
        raise HTTPException(
            status_code=500,
            detail="Tenant registry lookup failed",
        ) from exc


# =========================================================
# SCHEMA RESOLUTION
# =========================================================

def get_tenant_schema_name(db: Session, tenant_id: str) -> str:
    """
    ✅ SINGLE SOURCE OF TRUTH

    - Always returns public schema
    - Future-proof if multi-schema is reintroduced
    """
    return "public"


# =========================================================
# BACKWARD-COMPATIBILITY SHIM
# =========================================================

def assert_known_tenant(db: Session, tenant_id: str) -> None:
    """
    ✅ SAFE VALIDATION ENTRY POINT

    - Uses SAME session
    - Enforces existence + ACTIVE state
    - No hidden transactions
    """
    _ = get_tenant_by_id(db, tenant_id)