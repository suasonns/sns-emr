from __future__ import annotations

import logging
import os

from fastapi import Request
from fastapi.responses import JSONResponse

# ✅ Dedicated logger namespace
logger = logging.getLogger("sns_emr.access_control")

SUPPORT_PREFIX = "/support"


async def support_mfa_guard(request: Request, call_next):
    """
    ENTERPRISE CONTROL:

    OWNER-only support endpoints require MFA verification.

    Guarantees:
    - Only OWNER role allowed
    - MFA must be verified
    - Violations are logged (audit trail)
    - Dev bypass enabled for local testing
    """

    # ✅ DEV BYPASS (LOCAL ONLY)
    if os.getenv("ENV", "local").lower() == "local":
        return await call_next(request)

    path = request.url.path
    user = getattr(request.state, "user", None)

    if path.startswith(SUPPORT_PREFIX):

        # ✅ ROLE CHECK
        if not user or user.role != "OWNER":
            logger.warning(
                "🚫 Unauthorized support access attempt",
                extra={
                    "event": "support_access_denied",
                    "path": path,
                    "user_id": getattr(user, "id", None),
                    "role": getattr(user, "role", None),
                },
            )

            return JSONResponse(
                status_code=403,
                content={"detail": "Owner access required"},
            )

        # ✅ MFA CHECK
        if not getattr(request.state, "mfa_verified", False):
            logger.warning(
                "🔒 MFA required for support access",
                extra={
                    "event": "support_mfa_block",
                    "path": path,
                    "user_id": getattr(user, "id", None),
                },
            )

            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Multi-factor authentication required for support access"
                },
            )

    return await call_next(request)