"""
Tenant schema context (Phase 3 routing)

Enterprise behavior:
- Stores resolved tenant schema for the current request
- Default = None (fallback to public)
- Safe across async requests
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Optional


# =========================================================
# CONTEXT VARIABLE
# =========================================================

_current_tenant_schema: ContextVar[Optional[str]] = ContextVar(
    "current_tenant_schema",
    default=None,
)


# =========================================================
# VALIDATION
# =========================================================

def _validate_schema(schema_name: Optional[str]) -> Optional[str]:
    if schema_name is None:
        return None

    if not isinstance(schema_name, str):
        raise ValueError("schema_name must be a string or None")

    schema_name = schema_name.strip()

    if not schema_name:
        return None

    # ✅ simple safety rule (extend if needed)
    if not schema_name.replace("_", "").isalnum():
        raise ValueError("Invalid schema_name format")

    return schema_name


# =========================================================
# SETTER
# =========================================================

def set_current_tenant_schema(schema_name: Optional[str]) -> None:
    """
    Sets tenant schema for the current request.

    Must only be called from middleware.
    """

    validated = _validate_schema(schema_name)
    _current_tenant_schema.set(validated)


# =========================================================
# GETTER
# =========================================================

def get_current_tenant_schema() -> Optional[str]:
    """
    Returns current tenant schema.

    None → no tenant routing (public schema)
    """

    return _current_tenant_schema.get()


# =========================================================
# CLEAR (OPTIONAL HARDENING)
# =========================================================

def clear_current_tenant_schema() -> None:
    """
    Explicitly clears schema context.

    Recommended for middleware cleanup.
    """

    _current_tenant_schema.set(None)