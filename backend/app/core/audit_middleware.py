from __future__ import annotations

import time
from typing import Callable

from fastapi import Request, Response


async def audit_middleware(request: Request, call_next: Callable):
    """
    Enterprise-safe audit middleware.

    Critical rule:
    - NEVER mutate request.scope['headers'] or otherwise modify inbound headers.
      Auth dependencies rely on Authorization header.
    - If you need to log headers, copy them and redact the copy only.
    """

    start = time.time()

    # Copy headers for logging only (do not modify request.headers / scope)
    headers_for_log = dict(request.headers)

    # Redact auth token in logs (safe)
    if "authorization" in headers_for_log:
        headers_for_log["authorization"] = "REDACTED"

    try:
        response: Response = await call_next(request)
        return response
    finally:
        duration_ms = int((time.time() - start) * 1000)

        # NOTE:
        # If you already persist audit_logs here, keep doing it,
        # but only use headers_for_log (redacted copy).
        #
        # Example:
        # log_event(action="HTTP_REQUEST", meta={"path": str(request.url.path), "duration_ms": duration_ms, "headers": headers_for_log})
        #
        # Do NOT block response if logging fails.
        _ = duration_ms
        _ = headers_for_log