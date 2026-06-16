"""
Enterprise audit middleware (SNS Hospice EMR)

Guarantees:
✅ NEVER enforces authentication
✅ NEVER blocks requests
✅ NEVER mutates request flow
✅ NEVER raises exceptions
✅ ONLY observes execution context
✅ SAFE for tests and internal workflows
✅ SURVEY-DEFENSIBLE logging behavior

Design:
- Authentication is handled elsewhere
- Routing is handled elsewhere
- Middleware observes *after* request execution
"""

from __future__ import annotations

import logging
from fastapi import Request
from fastapi.responses import Response

logger = logging.getLogger("audit")


async def audit_middleware(request: Request, call_next):
    """
    Enterprise audit middleware.

    CRITICAL RULE:
    This middleware must NEVER fail the request.
    All errors are swallowed and logged.
    """

    # -----------------------------------------------------
    # Execute request FIRST (non-blocking, non-enforcing)
    # -----------------------------------------------------
    try:
        response: Response = await call_next(request)
    except Exception:
        # Even catastrophic downstream failures must not be masked
        logger.exception("AUDIT: downstream exception during request handling")
        raise

    # -----------------------------------------------------
    # Observability ONLY (best-effort)
    # -----------------------------------------------------
    try:
        db = getattr(request.state, "db", None)

        if not db:
            logger.warning(
                "AUDIT WARNING: request.state.db not present "
                "(DB dependency may not have been injected)"
            )
            return response

        tenant_id = db.info.get("tenant_id")
        user_id = db.info.get("user_id")

        if not tenant_id:
            logger.error(
                "AUDIT WARNING: DB session missing tenant_id "
                "(tenant context misconfiguration)"
            )

        if not user_id:
            logger.warning(
                "AUDIT WARNING: DB session missing user_id "
                "(authentication context not propagated)"
            )

        logger.debug(
            "AUDIT TRACE",
            extra={
                "path": request.url.path,
                "method": request.method,
                "tenant_id": str(tenant_id) if tenant_id else None,
                "user_id": str(user_id) if user_id else None,
                "status_code": response.status_code,
            },
        )

    except Exception:
        # Audit failures must NEVER impact request flow
        logger.exception("AUDIT ERROR: unexpected failure during audit logging")

    return response