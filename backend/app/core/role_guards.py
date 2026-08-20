from __future__ import annotations

from fastapi import Depends, HTTPException, status

from app.core.roles import is_owner_role
from app.core.security import CurrentUser, get_current_user


# =========================================================
# OWNER ROLE GUARD
# =========================================================

def require_owner(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """
    Enforces OWNER-level access.

    Enterprise guarantees:
    ✅ Uses authenticated JWT user
    ✅ Strong typing (CurrentUser)
    ✅ Compatible with FastAPI dependency system
    ✅ Returns user for downstream usage
    """

    if not is_owner_role(user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner access required",
        )

    return user