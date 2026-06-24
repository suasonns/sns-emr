from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import Dict

from fastapi import Request
from fastapi.responses import JSONResponse


# =========================================================
# CONFIGURATION
# =========================================================

IDLE_TIMEOUT_MINUTES = int(os.getenv("IDLE_TIMEOUT_MINUTES", "15"))
IDLE_TIMEOUT = timedelta(minutes=IDLE_TIMEOUT_MINUTES)

# Opportunistic cleanup settings
IDLE_CACHE_MAX_ENTRIES = int(os.getenv("IDLE_CACHE_MAX_ENTRIES", "10000"))
IDLE_CLEANUP_INTERVAL_SECONDS = int(os.getenv("IDLE_CLEANUP_INTERVAL_SECONDS", "300"))

# Bearer token -> last activity timestamp (UTC)
_last_activity: Dict[str, datetime] = {}

# Async lock for concurrent request safety inside one process
_last_activity_lock = asyncio.Lock()

# Timestamp of last cleanup pass
_last_cleanup_at: datetime | None = None


# =========================================================
# TIME HELPERS
# =========================================================

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


# =========================================================
# TOKEN EXTRACTION
# =========================================================

def _extract_bearer_token(request: Request) -> str | None:
    auth = request.headers.get("authorization")
    if not auth:
        return None

    parts = auth.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        token = parts[1].strip()
        return token or None

    return None


# =========================================================
# PUBLIC PATHS (NO IDLE TIMEOUT)
# =========================================================

def _is_public_path(path: str) -> bool:
    """
    Endpoints that must NOT be subject to idle timeout.
    """
    if path in ("/", "/health", "/openapi.json"):
        return True
    if path.startswith("/docs"):
        return True
    if path.startswith("/redoc"):
        return True
    if path.startswith("/auth/"):
        return True
    return False


# =========================================================
# CLEANUP
# =========================================================

def _should_cleanup(now: datetime) -> bool:
    global _last_cleanup_at

    if _last_cleanup_at is None:
        return True

    return (now - _last_cleanup_at).total_seconds() >= IDLE_CLEANUP_INTERVAL_SECONDS


def _expired_before(now: datetime) -> datetime:
    return now - IDLE_TIMEOUT


async def _cleanup_expired_sessions(now: datetime) -> None:
    """
    Removes expired token activity records opportunistically.
    Safe, lightweight, and bounded.
    """
    global _last_cleanup_at

    cutoff = _expired_before(now)

    async with _last_activity_lock:
        expired_tokens = [token for token, ts in _last_activity.items() if ts < cutoff]
        for token in expired_tokens:
            _last_activity.pop(token, None)

        # Emergency size guard: if still too large, trim oldest entries
        if len(_last_activity) > IDLE_CACHE_MAX_ENTRIES:
            sorted_items = sorted(_last_activity.items(), key=lambda x: x[1])
            overflow = len(_last_activity) - IDLE_CACHE_MAX_ENTRIES
            for token, _ in sorted_items[:overflow]:
                _last_activity.pop(token, None)

        _last_cleanup_at = now


# =========================================================
# MIDDLEWARE
# =========================================================

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

    # Opportunistic cleanup
    if _should_cleanup(now):
        await _cleanup_expired_sessions(now)

    async with _last_activity_lock:
        last = _last_activity.get(token)

        # Enforce idle timeout
        if last is not None and (now - last) > IDLE_TIMEOUT:
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