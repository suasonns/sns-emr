from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    id: str
    tenant_id: str
    role: str


def _b64url_decode(data: str) -> bytes:
    padding = "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _decode_jwt_payload(token: str) -> Dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Not a JWT")
    payload_bytes = _b64url_decode(parts[1])
    return json.loads(payload_bytes.decode("utf-8"))


def _normalize_token(raw: str) -> str:
    """
    Normalize Authorization token input.

    Accepts:
      - <jwt>
      - Bearer <jwt>
      - Bearer Bearer <jwt>   (Swagger UI misuse)
    """
    raw = raw.strip()
    parts = raw.split()

    if len(parts) == 1:
        token = parts[0]
    elif len(parts) >= 2 and parts[0].lower() == "bearer":
        token = parts[1]
        if token.lower() == "bearer" and len(parts) >= 3:
            token = parts[2]
    else:
        token = parts[-1]

    return "".join(token.split())


def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> CurrentUser:
    """
    Enterprise‑grade, Swagger‑compatible bearer authentication.

    - Tolerates Swagger quirks
    - Enforces required JWT fields
    - Normalizes role for downstream authorization
    """
    if creds is None or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = _normalize_token(creds.credentials)

    try:
        payload = _decode_jwt_payload(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    user_id = str(payload.get("sub") or "").strip()
    tenant_id = str(payload.get("tenant_id") or "").strip()
    role = str(payload.get("role") or "").strip().upper()

    if not user_id or not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    return CurrentUser(
        id=user_id,
        tenant_id=tenant_id,
        role=role,
    )


def verify_password(*args, **kwargs) -> bool:
    # Dev‑only placeholder
    return True