from __future__ import annotations

from contextvars import ContextVar
from typing import Optional
from uuid import UUID


# =========================================================
# CONTEXT VARIABLE
# =========================================================

_current_tenant_id: ContextVar[Optional[UUID]] = ContextVar(
    "current_tenant_id",
    default=None,
)


# =========================================================
# SETTER
# =========================================================

def set_current_tenant(tenant_id: Optional[UUID]) -> None:
    """
    Sets the current request tenant context.

    Safe for async / multi-request environments.
    Must only be called at request-boundary (middleware or auth layer).
    """
    if tenant_id is not None and not isinstance(tenant_id, UUID):
        raise ValueError("tenant_id must be a UUID or None")

    _current_tenant_id.set(tenant_id)


# =========================================================
# GETTER
# =========================================================

def get_current_tenant() -> Optional[UUID]:
    """
    Returns the current request tenant_id.

    Returns:
        UUID → when tenant context is set
        None → when no tenant context is available

    This function is SAFE to call anywhere in the application.
    """
    return _current_tenant_id.get()
