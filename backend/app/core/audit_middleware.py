from fastapi import Request
from fastapi.responses import Response
import logging

logger = logging.getLogger("audit")


async def audit_middleware(request: Request, call_next):
    """
    Enterprise audit middleware.

    - NEVER enforces tenant
    - NEVER reads headers
    - ONLY observes DB session
    """

    response: Response = await call_next(request)

    db = getattr(request.state, "db", None)
    if not db:
        return response

    if not db.info.get("tenant_id"):
        logger.error(
            "AUDIT: DB session missing tenant_id "
            "(miswired tenant-scoped endpoint)"
        )

    return response