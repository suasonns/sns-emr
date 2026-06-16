from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal


@dataclass(frozen=True)
class TenantRecord:
    tenant_id: str
    schema_name: str
    display_name: str
    status: str


def get_tenant_by_id(db: Session, tenant_id: str) -> TenantRecord:
    """
    ✅ CANONICAL TENANT REGISTRY (ENTERPRISE)

    - Single source of truth (DB-backed: core.tenants)
    - ACTIVE lifecycle enforced
    - SQLAlchemy 2.x safe (text())
    """
    stmt = text(
        """
        SELECT id, schema_name, display_name, status
        FROM core.tenants
        WHERE id = :tenant_id
        """
    )
    row = db.execute(stmt, {"tenant_id": tenant_id}).fetchone()

    if not row:
        raise RuntimeError(f"Unknown tenant_id: {tenant_id}")

    if row.status != "ACTIVE":
        raise RuntimeError(f"Tenant not active: {tenant_id}")

    return TenantRecord(
        tenant_id=str(row.id),
        schema_name=row.schema_name,
        display_name=row.display_name,
        status=row.status,
    )


def get_tenant_schema_name(db: Session, tenant_id: str) -> str:
    """
    ✅ ONLY approved way to resolve tenant schema name (DB-backed)
    """
    return get_tenant_by_id(db, tenant_id).schema_name


def assert_known_tenant(tenant_id: str) -> None:
    """
    ✅ BACKWARD-COMPATIBILITY SHIM (DO NOT USE IN NEW CODE)

    Some legacy routers import assert_known_tenant at module import time.
    This function exists ONLY to prevent startup crashes and to provide
    the same safety boundary: tenant must exist and be ACTIVE.

    New code should NOT call this; it should call:
        get_tenant_schema_name(db, tenant_id)
    """
    db: Session = SessionLocal()
    try:
        _ = get_tenant_by_id(db, tenant_id)
    finally:
        db.close()