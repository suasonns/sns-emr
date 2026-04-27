from fastapi import Depends, HTTPException, status
from typing import List
from app.core.auth import get_current_user, CurrentUser


def require_roles(allowed_roles: List[str]):
    def checker(user: CurrentUser = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return checker