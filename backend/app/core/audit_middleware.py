from fastapi import Request
from app.core.auth import get_current_user
from app.services.audit_logger import log_event


async def audit_middleware(request: Request, call_next):
    """
    Audit all incoming API requests.
    """
    response = await call_next(request)

    try:
        user = await get_current_user(request)
        log_event(
            user_id=user.user_id,
            role=user.role,
            action=f"{request.method} {request.url.path}",
            ip_address=request.client.host if request.client else None,
        )
    except Exception:
        # Anonymous or failed auth requests are not logged here
        pass

    return response