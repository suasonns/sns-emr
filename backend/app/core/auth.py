from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from app.core.security import SECRET_KEY, ALGORITHM, JWT_AUDIENCE, JWT_ISSUER


security = HTTPBearer()


# =========================================================
# CONSTANTS
# =========================================================

VALID_ROLES = {
    "RN",
    "LVN",
    "LPN",
    "MD",
    "NP",
    "SW",
    "CHAPLAIN",
    "MEDICAL_DIRECTOR",
    "ALTERNATE_MEDICAL_DIRECTOR",
    "MEDICAL_DIRECTOR_DESIGNEE",
    "ADMINISTRATOR",
    "DPCS",
}


# =========================================================
# USER CONTEXT
# =========================================================

@dataclass(frozen=True)
class CurrentUser:
    user_id: uuid.UUID
    role: str
    tenant_id: Optional[uuid.UUID] = None
    email: Optional[str] = None
    is_system: bool = False


# =========================================================
# TOKEN DECODE
# =========================================================

def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


# =========================================================
# DEPENDENCY
# =========================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:

    token = credentials.credentials
    payload = _decode_token(token)

    user_id = payload.get("sub")
    role = payload.get("role")
    tenant_id = payload.get("tenant_id")

    if not user_id or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing required claims",
        )

    if role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Invalid role: {role}",
        )

    try:
        return CurrentUser(
            user_id=uuid.UUID(user_id),
            role=str(role),
            tenant_id=uuid.UUID(tenant_id) if tenant_id else None,
            email=payload.get("email"),
            is_system=False,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token values",
        )