from fastapi import Request
from fastapi.responses import Response
import logging

logger = logging.getLogger("audit")


async def audit_middleware(request: Request, call_next):
    """
    Enterprise audit middleware

    Guarantees:
    ✅ NEVER enforces authentication
    ✅ NEVER blocks requests (prevents 401 leakage)
    ✅ NEVER mutates request flow
    ✅ ONLY observes execution context
    ✅ SAFE for tests and internal workflows

    Design:
    - Authentication is handled elsewhere (if required)
    - Middleware only inspects state after route execution
    """

    # -----------------------------------------------------
    # Execute request FIRST (non-blocking)
    # -----------------------------------------------------
    response: Response = await call_next(request)

    # -----------------------------------------------------
    # Observability only (no enforcement)
    # -----------------------------------------------------
    db = getattr(request.state, "db", None)

    if db:
        tenant_id = db.info.get("tenant_id")

        if not tenant_id:
            logger.error(
                "AUDIT WARNING: DB session missing tenant_id "
                "(tenant context misconfiguration)"
            )

    return response