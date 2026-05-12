from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Dict

from fastapi import Request
from fastapi.responses import JSONResponse


# ---------------------------------
# CONFIGURATION
# ---------------------------------
IDLE_TIMEOUT = timedelta(minutes=15)

# Bearer token -> last activity timestamp (UTC)
_last_activity: Dict[str, datetime] = {}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _extract_bearer_token(request: Request) -> str | None:
    auth = request.headers.get("authorization")
    if not auth:
        return None
    parts = auth.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return None


def _is_public_path(path: str) -> bool:
    """
    Endpoints that must NOT be subject to idle timeout.
    """
    if path in ("/", "/health", "/openapi.json"):
        return True
    if path.startswith("/docs"):
        return True
    if path.startswith("/auth/"):
        return True
    return False


async def idle_timeout_middleware(request: Request, call_next):
    path = request.url.path

    # Skip public / unauthenticated paths
    if _is_public_path(path):
        return await call_next(request)

    token = _extract_bearer_token(request)
    if not token:
        # Let auth dependencies handle missing tokens
        return await call_next(request)

    now = _now_utc()
    last = _last_activity.get(token)

    # Enforce idle timeout
    if last is not None:
        if (now - last) > IDLE_TIMEOUT:
            # Expire session
            _last_activity.pop(token, None)
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Session expired due to inactivity. Please log in again."
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Update last activity
    _last_activity[token] = now

    return await call_next(request)