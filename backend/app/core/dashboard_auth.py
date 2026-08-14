from __future__ import annotations

from fastapi import HTTPException, status

from app.core.auth import CurrentUser

ALLOWED_DASHBOARD_ROLES = {
    "OWNER",
    "ADMINISTRATOR",
    "DPCS",
    "RN",
}


def resolve_dashboard_user(current_user: CurrentUser) -> CurrentUser:
    """Require an authenticated user with a valid dashboard role."""
    if current_user.role not in ALLOWED_DASHBOARD_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not authorized for dashboard access",
        )
    return current_user
