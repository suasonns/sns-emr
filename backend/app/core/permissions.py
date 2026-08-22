from __future__ import annotations

from typing import Iterable, Optional

from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user, CurrentUser
from app.core.security import get_current_access
from app.core.roles import role_matches


# =========================================================
# SYSTEM ACCESS (INFRA / ADMIN ONLY)
# =========================================================

def require_system_access():
    """
    System-level access ONLY.

    Use ONLY for:
    - /admin/*
    - /debug/*
    - /system/*

    NEVER use this in clinical endpoints.
    """

    def dependency(access=Depends(get_current_access)):
        return access

    return dependency


# =========================================================
# ROLE-BASED ACCESS (CLINICAL)
# =========================================================

def require_roles(
    allowed_roles: Optional[Iterable[str]] = None,
    *,
    allow_clinical_admin: bool = True,
):
    """
    Enforces role-based access using JWT user context.

    Use this for ALL clinical endpoints:
    - visits
    - notes
    - F2F
    - certifications
    - tasks

    `allow_clinical_admin` controls whether ADMINISTRATOR/DPCS/DPCS_ADMINISTRATOR
    implicitly satisfy this gate (see `role_matches`). Set it to False for
    endpoints that grant an actual clinical/legal signing authority (e.g.
    physician order approval, batch signature) — administrative rank must
    never itself confer the ability to sign as a prescriber. Leave it True
    (default) for viewing/monitoring endpoints, where oversight roles are
    intentionally allowed to satisfy the gate.
    """

    def dependency(user: CurrentUser = Depends(get_current_user)):
        if not role_matches(
            user.role, allowed_roles, allow_clinical_admin=allow_clinical_admin
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' not allowed",
            )
        return user

    return dependency


# =========================================================
# PERMISSION-BASED ACCESS (FUTURE)
# =========================================================

def require_permission(permission: str = ""):
    """
    Placeholder for fine-grained permissions.
    Currently acts as authenticated user gate.
    """

    def dependency(user: CurrentUser = Depends(get_current_user)):
        return user

    return dependency


# =========================================================
# PERMISSION CHECK (UTILITY)
# =========================================================

def has_permission(*args, **kwargs) -> bool:
    """
    Placeholder permission check.
    """
    return True
