from __future__ import annotations

import logging
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.roles import BILLING_DEPARTMENT_ROLES, is_platform_role, normalize_role
from app.core.security import decode_access_token

logger = logging.getLogger("sns_emr.access_control")

CLINICAL_PREFIXES = (
    "/patients",
    "/visits",
    "/notes",
    "/clinical",
    "/api/patients",
    "/api/clinical",
    "/api/dashboard/tenant",
    "/api/dashboard/clinical",
    "/api/census",
    "/api/idg",
    "/api/admission",
    "/api/med",
    "/api/safety",
    "/api/communications",
)

PLATFORM_ALLOWED_PREFIXES = (
    "/auth",
    "/api/owner",
    "/api/dashboard/owner",
    "/api/support",
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
    platform_route_allowed = any(
        _matches_prefix(path, prefix) for prefix in PLATFORM_ALLOWED_PREFIXES
    )
    clinical_route = any(_matches_prefix(path, prefix) for prefix in CLINICAL_PREFIXES)

    if is_platform_role(role) and platform_route_allowed:
        return await call_next(request)
    if not is_platform_role(role) and (
        role not in BILLING_DEPARTMENT_ROLES or not clinical_route
    ):
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
