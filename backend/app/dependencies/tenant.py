# app/dependencies/tenant.py

from uuid import UUID
from fastapi import Depends, HTTPException

from app.dependencies.auth import get_current_user
from app.core.tenant_context import set_current_tenant


def inject_tenant(current_user=Depends(get_current_user)):
    """
    Request-scoped tenant context injection.

    Uses yield so tenant stays set for the whole request.
    Avoids ContextVar token reset (which can fail under threadpool contexts).
    """
    tenant_id = getattr(current_user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant not found")

    set_current_tenant(UUID(str(tenant_id)))
    try:
        yield tenant_id
    finally:
        set_current_tenant(None)
