from __future__ import annotations

import time
import uuid
from datetime import datetime
from typing import Callable

from fastapi import Request, Response

from app.services.audit_logger import log_event
from app.core.database import SessionLocal


async def audit_middleware(request: Request, call_next: Callable):
    request_id = str(uuid.uuid4())
    start = time.time()

    headers_for_log = dict(request.headers)
    if "authorization" in headers_for_log:
        headers_for_log["authorization"] = "REDACTED"

    status_code = 500

    try:
        response: Response = await call_next(request)
        status_code = response.status_code
        return response

    finally:
        duration_ms = int((time.time() - start) * 1000)

        tenant_id = getattr(request.state, "tenant_id", None)
        user_id = getattr(request.state, "user_id", None)
        client_ip = request.client.host if request.client else "unknown"

        metadata = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "path": request.url.path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "client_ip": client_ip,
            "headers": headers_for_log,
        }

        try:
            db = SessionLocal()
            try:
                log_event(
                    request_id=request_id,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    role=None,
                    action="HTTP_REQUEST",
                    entity_type="api_call",
                    entity_id=request.url.path,
                    ip=client_ip,
                    metadata=metadata,
                    db=db,
                    commit=True,  # ✅ critical fix
                )
            finally:
                db.close()
        except Exception:
            pass