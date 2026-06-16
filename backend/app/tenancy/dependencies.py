from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user
from app.tenancy.registry import assert_known_tenant, get_tenant_schema
from app.tenancy.search_path import set_tenant_search_path
from app.db.session import get_db


def require_valid_tenant(
    db = Depends(get_db),
    user = Depends(get_current_user),
):
    """
    Enterprise-grade tenant safety guard + schema routing.
    """

    tenant_id = getattr(user, "tenant_id", None)
    if tenant_id is None and isinstance(user, dict):
        tenant_id = user.get("tenant_id")

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing tenant context",
        )

    try:
        # ✅ Validates tenant exists
        tenant = assert_known_tenant(str(tenant_id))
        # tenant.schema_name should come from canonical registry
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )

    # ✅ THIS IS THE SYSTEM FIX
    set_tenant_search_path(db, tenant.schema_name)

    return user