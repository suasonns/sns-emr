"""
Tenant routing middleware (Phase 3)

Enterprise guarantees:
- Feature-flagged (TENANT_ROUTING_ENABLED)
- Read-only lookup in core.tenants via resolve_tenant_schema
- No schema switching here (only sets ContextVar)
- search_path is applied inside get_db() using SET LOCAL (request scoped)
- Safe fallback: None -> public
"""

from __future__ import annotations

from typing import Optional
from fastapi import Request

from app.core.database import TENANT_ROUTING_ENABLED, SessionLocal
from app.core.tenant_resolver import resolve_tenant_schema
from app.core.tenant_schema_context import set_current_tenant_schema


def _normalize_tenant_code(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    value = value.strip()
    return value.upper() if value else None


async def tenant_routing_middleware(request: Request, call_next):
    # Default: do nothing (behavior unchanged)
    if not TENANT_ROUTING_ENABLED:
        return await call_next(request)

    tenant_code = _normalize_tenant_code(request.headers.get("X-Tenant-Code"))

    db = SessionLocal()
    try:
        schema_name = resolve_tenant_schema(db=db, tenant_code=tenant_code)
        # Store schema for this request context; None means fallback to public
        set_current_tenant_schema(schema_name)
        response = await call_next(request)
        return response
    finally:
        # Always clear schema context after request completes
        set_current_tenant_schema(None)
        db.close()
