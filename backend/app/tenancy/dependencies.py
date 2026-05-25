from fastapi import Depends, HTTPException, status

from app.tenancy.registry import assert_known_tenant

# Use whichever get_current_user your app already uses.
# You have both patterns in your repo history; this is the one used in visits.py.
from app.core.security import get_current_user


def require_valid_tenant(user=Depends(get_current_user)):
    """
    Global tenant safety guard:
    - requires tenant_id present
    - requires tenant_id in canonical registry
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
        assert_known_tenant(str(tenant_id))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )

    return user