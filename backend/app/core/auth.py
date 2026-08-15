"""
DEPRECATED

DO NOT ADD NEW IMPORTS FROM THIS FILE.

Migration target:
app.core.security

Scheduled for removal after all dependencies migrated.
"""

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

def get_current_user(*args, **kwargs):
    raise RuntimeError(
        "Legacy auth.py get_current_user called. "
        "Use app.core.security.get_current_user"
    )