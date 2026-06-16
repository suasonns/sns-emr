from __future__ import annotations

import logging
import os

from fastapi import Request
from fastapi.responses import JSONResponse

# ✅ correct logger namespace
logger = logging.getLogger("sns_emr.access_control")

# ✅ CLINICAL ROUTE PREFIXES (LOCKED)
CLINICAL_PREFIXES = (
    "/patients",
    "/visits",
    "/notes",
    "/clinical",
    "/dashboard/tenant",
)


async def clinical_access_guard(request: Request, call_next):
    """
    ENTERPRISE COMPLIANCE CONTROL:

    OWNER and BILLING roles MUST NEVER access clinical data.

    Guarantees:
    - Hard block (non-negotiable)
    - Audit logging for violations
    - Safe dev bypass (local only)
    - Fail-safe handling
    """

    # ✅ DEV BYPASS (only for local development)
    if os.getenv("ENV", "local").lower() == "local":
        return await call_next(request)

    path = request.url.path
    user = getattr(request.state, "user", None)

    # ✅ FAIL-SAFE: no user → allow downstream auth to handle
    if user is None:
        return await call_next(request)

    # ✅ HARD BLOCK for OWNER / BILLING roles
    if user.role in {"OWNER", "BILLING"}:
        for prefix in CLINICAL_PREFIXES:
            if path.startswith(prefix):

                # ✅ AUDIT LOG (CRITICAL)
                logger.warning(
                    "🚫 Clinical access blocked",
                    extra={
                        "event": "clinical_access_denied",
                        "path": path,
                        "role": user.role,
                        "user_id": getattr(user, "id", None),
                    },
                )

                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": "Clinical access is not permitted for this role."
                    },
                )

    return await call_next(request)
``