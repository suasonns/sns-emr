from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user
from app.tenancy.registry import assert_known_tenant


def require_valid_tenant(user=Depends(get_current_user)):
    """
    Enterprise-grade tenant safety guard.

    Enforces:
    - authenticated user
    - tenant_id present on user
    - tenant_id exists in canonical tenant registry

    Returns:
    - user object (unchanged)
    """

    # Normalize tenant_id access
    tenant_id = getattr(user, "tenant_id", None)
    if tenant_id is None and isinstance(user, dict):
        tenant_id = user.get("tenant_id")

    # Missing tenant context → auth failure
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing tenant context",
        )

    # Unknown tenant → forbidden
    try:
        assert_known_tenant(str(tenant_id))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )

    return user