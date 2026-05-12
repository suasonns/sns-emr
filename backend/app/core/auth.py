import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from app.core.security import SECRET_KEY, ALGORITHM

security = HTTPBearer()


# ✅ Canonical allowed roles (include RN)
ALLOWED_ROLES = {
    "RN",                 # ✅ REQUIRED (your dev + clinical usage)
    "RN_CASE_MANAGER",
    "RN_ADMIN",
    "DPCS",
    "LVN",
    "LPN",
    "MD",
    "NP",
    "SW",
    "CHAPLAIN",
}


class CurrentUser:
    def __init__(self, user_id: uuid.UUID, role: str):
        self.user_id = user_id
        self.id = user_id          # ✅ compatibility across routers
        self.role = role


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        sub = payload.get("sub")
        role = payload.get("role")

        if not sub or not role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        # ✅ Normalize role defensively
        role = role.strip().upper()

        if role not in ALLOWED_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid user role",
            )

        try:
            user_id = uuid.UUID(sub)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token subject (sub must be UUID)",
            )

        return CurrentUser(user_id=user_id, role=role)

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
