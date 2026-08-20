from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext


# =========================================================
# CONFIG
# =========================================================

APP_ENV = (os.getenv("APP_ENV") or os.getenv("ENV") or os.getenv("ENVIRONMENT") or "production").lower()

SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)

JWT_ISSUER = os.getenv("JWT_ISSUER", "sns-hospice-solutions")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "sns-hospice-solutions-users")

AUTH_MODE = os.getenv("AUTH_MODE", "TOKEN").upper()
SYSTEM_ACCESS_KEY = os.getenv("SYSTEM_ACCESS_KEY", "")

ALLOWED_AUTH_MODES = {"TOKEN", "SYSTEM"}

if AUTH_MODE not in ALLOWED_AUTH_MODES:
    raise RuntimeError(f"Invalid AUTH_MODE: {AUTH_MODE}")

if APP_ENV != "development":
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY must be configured outside development")

    if len(SECRET_KEY) < 32:
        raise RuntimeError(
            "SECRET_KEY must be configured and >= 32 characters"
        )

    if AUTH_MODE != "TOKEN":
        raise RuntimeError("Production requires AUTH_MODE=TOKEN")

    if AUTH_MODE == "SYSTEM" and not SYSTEM_ACCESS_KEY:
        raise RuntimeError(
            "SYSTEM_ACCESS_KEY must be configured when AUTH_MODE=SYSTEM"
        )


# =========================================================
# CONTEXT OBJECTS
# =========================================================

@dataclass(frozen=True)
class CurrentUser:
    user_id: UUID
    role: str
    tenant_id: UUID
    email: Optional[str] = None
    is_system: bool = False


@dataclass(frozen=True)
class SystemAccessContext:
    source: str = "system"
    is_system: bool = True


# =========================================================
# SYSTEM ACCESS
# =========================================================

def get_current_access(
    x_system_key: str = Header(..., alias="X-System-Key"),
) -> SystemAccessContext:
    if not SYSTEM_ACCESS_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System access not configured",
        )

    if x_system_key != SYSTEM_ACCESS_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="System access denied",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return SystemAccessContext()


# =========================================================
# JWT HELPERS
# =========================================================

bearer_scheme = HTTPBearer(auto_error=False)

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def _require_secret_key() -> None:
    if not SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SECRET_KEY is not configured",
        )

    if len(SECRET_KEY) < 32:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SECRET_KEY must be configured and >= 32 characters",
        )


def create_access_token(
    *,
    user_id: UUID,
    role: str,
    tenant_id: UUID,
    expires_delta: Optional[timedelta] = None,
    email: Optional[str] = None,
) -> str:
    _require_secret_key()

    now = datetime.now(timezone.utc)

    expire = now + (
        expires_delta
        or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": str(role).strip().upper(),
        "typ": "access",
        "jti": str(uuid4()),
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    if email:
        payload["email"] = email

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password_hash(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a JWT access token.
    """
    _require_secret_key()

    try:
        payload = jwt.decode(
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
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("typ") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


# =========================================================
# CURRENT USER
# =========================================================

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> CurrentUser:
    """
    Clinical user dependency.
    Use for patient/visit/note/task/CTI/F2F endpoints.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    if AUTH_MODE != "TOKEN":

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Clinical user authentication is disabled",
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(
        credentials.credentials
    )

    subject = payload.get("sub")
    role = payload.get("role")
    tenant_id = payload.get("tenant_id")

    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing sub claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing role claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing tenant_id claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = UUID(str(subject))
        tenant_uuid = UUID(str(tenant_id))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid UUID claims",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return CurrentUser(
        user_id=user_uuid,
        role=str(role).strip().upper(),
        tenant_id=tenant_uuid,
        email=payload.get("email"),
        is_system=False,
    )