from __future__ import annotations

from typing import Callable

from fastapi import Depends, HTTPException, status

from app.core.roles import is_owner_role, is_platform_role, role_can
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


# =========================================================
# SNS STAFF & ACCESS — CAPABILITY GUARD (Phase UM-1)
#
# Deny-by-default RBAC dependency for the "SNS Staff & Access" surface
# (backend/app/api/owner_admin.py). Every capability listed in
# app.core.roles.STAFF_CAPABILITIES is enforced here via role_can(), which
# is the single authoritative permission mapping — this dependency does not
# duplicate or re-derive any permission logic itself. Target-hierarchy
# (assignment-ceiling / final-active-owner) checks that require reading the
# target's role from the database happen at the endpoint layer, in addition
# to this actor-level check, per the "no button-only security" requirement.
# =========================================================

def require_platform_permission(capability: str) -> Callable[..., CurrentUser]:
    def _dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not is_platform_role(user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Platform staff access required",
            )
        if not role_can(user.role, capability):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required platform permission: {capability}",
            )
        return user

    return _dependency