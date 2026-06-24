from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt


# =========================================================
# CONFIG
# =========================================================

APP_ENV = os.getenv("APP_ENV", "development").lower()

SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

JWT_ISSUER = os.getenv("JWT_ISSUER", "sns-emr")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "sns-emr-users")

AUTH_MODE = os.getenv("AUTH_MODE", "TOKEN").upper()
SYSTEM_ACCESS_KEY = os.getenv("SYSTEM_ACCESS_KEY", "")

ALLOWED_AUTH_MODES = {"TOKEN", "SYSTEM"}

if AUTH_MODE not in ALLOWED_AUTH_MODES:
    raise RuntimeError(f"Invalid AUTH_MODE: {AUTH_MODE}")

# Fail closed outside development
if APP_ENV != "development":
    if not SECRET_KEY or len(SECRET_KEY) < 32:
        raise RuntimeError("SECRET_KEY must be set and at least 32 characters outside development")

    if AUTH_MODE == "SYSTEM" and not SYSTEM_ACCESS_KEY:
        raise RuntimeError("SYSTEM_ACCESS_KEY must be set when AUTH_MODE=SYSTEM outside development")


# =========================================================
# CONTEXT OBJECTS
# =========================================================

@dataclass(frozen=True)
class CurrentUser:
    user_id: UUID
    role: str
    tenant_id: UUID
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_system: bool = False


@dataclass(frozen=True)
class SystemAccessContext:
    source: str = "system"
    is_system: bool = True


# =========================================================
# SYSTEM ACCESS (INFRA / ADMIN ONLY)
# =========================================================

def get_current_access(
    x_system_key: str = Header(..., alias="X-System-Key"),
) -> SystemAccessContext:
    """
    Intended only for infra/admin endpoints.
    Do NOT use this for clinical user endpoints.
    """
    if not SYSTEM_ACCESS_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System access is not configured",
        )

    if x_system_key != SYSTEM_ACCESS_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="System access denied",
        )

    return SystemAccessContext()


# =========================================================
# JWT HELPERS
# =========================================================

bearer_scheme = HTTPBearer(auto_error=True)


def create_access_token(
    *,
    subject: str,
    role: str,
    tenant_id: str,
    expires_delta: Optional[timedelta] = None,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
) -> str:
    """
    Creates a signed JWT access token for a clinical user.
    """
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    payload: Dict[str, Any] = {
        "sub": subject,
        "role": role,
        "tenant_id": tenant_id,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    if email:
        payload["email"] = email
    if full_name:
        payload["full_name"] = full_name

    if not SECRET_KEY or len(SECRET_KEY) < 32:
        if APP_ENV != "development":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SECRET_KEY must be set and at least 32 characters",
            )

    return jwt.encode(payload, SECRET_KEY or "DEV_ONLY_CHANGE_ME_NOW_32CHARS_MIN", algorithm=ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a JWT access token.
    """
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY or "DEV_ONLY_CHANGE_ME_NOW_32CHARS_MIN",
            algorithms=[ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


# =========================================================
# CLINICAL USER DEPENDENCY (TOKEN MODE)
# =========================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    """
    Clinical user dependency.
    Use for patient/visit/note/task/CTI/F2F endpoints.
    """
    if AUTH_MODE != "TOKEN":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Clinical user auth is not enabled in current AUTH_MODE",
        )

    token = credentials.credentials
    payload = decode_access_token(token)

    subject = payload.get("sub")
    role = payload.get("role")
    tenant_id = payload.get("tenant_id")

    if not subject or not role or not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing required claims",
        )

    try:
        user_id = UUID(str(subject))
        tenant_uuid = UUID(str(tenant_id))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token claims contain invalid UUIDs",
        )

    return CurrentUser(
        user_id=user_id,
        role=str(role),
        tenant_id=tenant_uuid,
        email=payload.get("email"),
        full_name=payload.get("full_name"),
        is_system=False,
    )