# app/core/permissions.py

from typing import Iterable, Optional
from fastapi import Depends, HTTPException, status

from app.core.security import get_current_access


def require_system_access():
    """
    Enforces system-level access ONLY.
    This is NOT a user, role, or clinician.
    """

    def _dependency(access=Depends(get_current_access)):
        if access.get("access_type") != "SYSTEM":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="System access required",
            )
        return access

    return _dependency


# ------------------------------------------------------------------
# Legacy compatibility shims (NO roles / NO permissions enforced)
# ------------------------------------------------------------------

def require_roles(_allowed_roles: Optional[Iterable[str]] = None):
    return require_system_access()


def require_permission(_permission: str = ""):
    return require_system_access()


def has_permission(*args, **kwargs):
    return True