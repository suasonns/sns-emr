from __future__ import annotations

import logging
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.roles import access_scope_for_role, normalize_role
from app.core.security import decode_access_token

logger = logging.getLogger("sns_emr.access_control")

PLATFORM_ALLOWED_PREFIXES = (
    "/auth",
    "/api/owner",
    "/api/dashboard/owner",
    "/api/dashboard/billing-readiness",
    "/api/support",
    "/health",
    "/ready",
)

BILLING_ALLOWED_PREFIXES = (
    "/auth",
    "/billing",
    "/api/dashboard/billing",
    "/api/dashboard/claim-lifecycle",
    "/health",
    "/ready",
)


def _matches_prefix(path: str, prefix: str) -> bool:
    return path == prefix or path.startswith(f"{prefix}/")


async def clinical_access_guard(request: Request, call_next):
    path = request.url.path
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return await call_next(request)

    try:
        payload = decode_access_token(token)
    except HTTPException:
        return await call_next(request)

    role = normalize_role(payload.get("role"))
    access_scope = access_scope_for_role(role)
    platform_route_allowed = any(
        _matches_prefix(path, prefix) for prefix in PLATFORM_ALLOWED_PREFIXES
    )
    billing_route_allowed = any(
        _matches_prefix(path, prefix) for prefix in BILLING_ALLOWED_PREFIXES
    )

    if access_scope == "tenant":
        return await call_next(request)
    if role == "PLATFORM_BILLING" and billing_route_allowed:
        return await call_next(request)
    if access_scope == "platform" and platform_route_allowed:
        return await call_next(request)
    if access_scope == "billing" and billing_route_allowed:
        return await call_next(request)

    logger.warning(
        "Clinical access blocked",
        extra={
            "event": "clinical_access_denied",
            "path": path,
            "role": role,
            "user_id": payload.get("sub"),
        },
    )
    return JSONResponse(
        status_code=403,
        content={"detail": "Clinical access is not permitted for this role."},
    )
