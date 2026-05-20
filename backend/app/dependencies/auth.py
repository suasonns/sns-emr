# app/dependencies/auth.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    """
    Minimal current user context.

    This is intentionally lightweight to avoid coupling startup to a full auth stack.
    Expand fields later as needed (roles, permissions, etc.).
    """
    id: str
    tenant_id: str


def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> CurrentUser:
    """
    Startup-safe authentication dependency.

    Behavior:
      - If no Bearer token is provided, raise 401.
      - If a token is provided, return a minimal CurrentUser context.

    NOTE:
      - This does NOT validate JWT signatures yet.
      - It exists to keep the app importable and enforce basic auth gating.
      - Replace with real JWT validation when ready (without changing API modules).
    """
    if creds is None or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    # Minimal parsing / placeholder context.
    # In production, replace this with proper JWT verification and tenant extraction.
    token = creds.credentials.strip()

    # Safe default placeholder values:
    # - keep deterministic and non-crashing
    # - do not infer clinical role or permissions here
    user_id = "authenticated-user"
    tenant_id = "default-tenant"

    # Optional: if you pass a simple token format like "user:<id>|tenant:<id>",
    # you can decode it deterministically without secrets (still not JWT).
    try:
        parts = [p.strip() for p in token.split("|") if p.strip()]
        for p in parts:
            if p.lower().startswith("user:"):
                user_id = p.split(":", 1)[1].strip() or user_id
            if p.lower().startswith("tenant:"):
                tenant_id = p.split(":", 1)[1].strip() or tenant_id
    except Exception:
        # Fail closed on auth format parsing issues
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token format",
        )

    return CurrentUser(id=user_id, tenant_id=tenant_id)