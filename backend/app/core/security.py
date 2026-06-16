# app/core/security.py

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import Header, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------

SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_ME_LATER")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# ✅ ENTERPRISE FIX — NEVER DEFAULT TO SYSTEM
AUTH_MODE = os.getenv("AUTH_MODE", "TOKEN").upper()

SYSTEM_ACCESS_KEY = os.getenv("SYSTEM_ACCESS_KEY", "CHANGE_ME_SYSTEM_KEY")

JWT_ISSUER = os.getenv("JWT_ISSUER", "sns-emr")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "sns-emr-users")

# -------------------------------------------------------------------
# VALIDATE AUTH MODE (FAIL FAST)
# -------------------------------------------------------------------

if AUTH_MODE not in {"TOKEN", "SYSTEM"}:
    raise RuntimeError(f"Invalid AUTH_MODE: {AUTH_MODE}")

# -------------------------------------------------------------------
# CONTEXT OBJECTS
# -------------------------------------------------------------------

class SystemAccessContext(dict):
    """
    Represents system-level access ONLY.
    Never used for clinical chart access.
    """
    pass


class CurrentUser:
    """
    Represents an authenticated clinical user (multi-tenant).
    """

    def __init__(self, user_id: uuid.UUID, role: str, tenant_id: uuid.UUID):
        self.user_id = user_id
        self.id = user_id  # compatibility
        self.role = role
        self.tenant_id = tenant_id


# -------------------------------------------------------------------
# SYSTEM ACCESS (INFRA ONLY)
# -------------------------------------------------------------------

def get_current_access(
    x_system_key: str = Header(..., alias="X-System-Key"),
) -> SystemAccessContext:
    if x_system_key != SYSTEM_ACCESS_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="System access denied",
        )

    return SystemAccessContext(
        access_type="SYSTEM",
        access_level="INTERNAL",
    )


# -------------------------------------------------------------------
# JWT HELPERS
# -------------------------------------------------------------------

bearer_scheme = HTTPBearer(auto_error=True)


def create_access_token(
    *,
    subject: str,
    role: str,
    tenant_id: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    if not SECRET_KEY or len(SECRET_KEY) < 32:
        if os.getenv("APP_ENV", "development").lower() != "development":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SECRET_KEY must be set and at least 32 characters",
            )

    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload: Dict[str, Any] = {
        "sub": subject,
        "role": role,
        "tenant_id": tenant_id,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
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


# -------------------------------------------------------------------
# CLINICAL USER DEPENDENCY (TOKEN ONLY)
# -------------------------------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    """
    TOKEN mode only.
    Used by ALL clinical / patient / visit / chart endpoints.
    """

    # ✅ HARD BLOCK SYSTEM MODE FOR CLINICAL ACCESS
    if AUTH_MODE != "TOKEN":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AUTH_MODE misconfigured for clinical access: {AUTH_MODE}",
        )

    payload = decode_access_token(credentials.credentials)

    sub = payload.get("sub")
    role = payload.get("role")
    tenant_id = payload.get("tenant_id")

    if not sub or not role or not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing required claims",
        )

    return CurrentUser(
        user_id=uuid.UUID(sub),
        role=str(role),
        tenant_id=uuid.UUID(tenant_id),
    )