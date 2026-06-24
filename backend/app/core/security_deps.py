from __future__ import annotations

from fastapi import Depends

from app.core.security import CurrentUser, get_current_user


def get_current_user_id(
    user: CurrentUser = Depends(get_current_user),
) -> str:
    """
    Returns the authenticated clinical user's UUID as a stable string.
    """
    return str(user.user_id)