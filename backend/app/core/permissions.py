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

def require_roles(allowed_roles: Optional[Iterable[str]] = None):
    """
    Enforces role-based access using JWT user context.

    Use this for ALL clinical endpoints:
    - visits
    - notes
    - F2F
    - certifications
    - tasks
    """

    def dependency(user: CurrentUser = Depends(get_current_user)):
        if not role_matches(user.role, allowed_roles):
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
