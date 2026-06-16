from __future__ import annotations

from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import get_current_user
from app.tenancy.registry import assert_known_tenant, get_tenant_schema_name
from app.tenancy.search_path import set_tenant_search_path


def get_db_tenant(
    user=Depends(get_current_user),
) -> Generator[Session, None, None]:
    """
    Tenant-aware DB session dependency (schema-per-tenant).
    Sets search_path to <tenant_schema>, public for this transaction/session.
    """
    tenant_id = getattr(user, "tenant_id", None)
    if not tenant_id:
        raise RuntimeError("Authenticated user missing tenant_id")

    # Validate tenant is real/known
    assert_known_tenant(str(tenant_id))

    # Resolve schema name from canonical registry
    tenant_schema = get_tenant_schema_name(str(tenant_id))

    db: Session = SessionLocal()
    try:
        # Apply tenant routing at the DB session level
        set_tenant_search_path(db, tenant_schema)
        yield db
    finally:
        db.close()