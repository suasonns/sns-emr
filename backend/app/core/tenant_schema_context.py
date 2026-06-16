"""
Tenant schema context (Phase 3 routing)

Enterprise behavior:
- Stores the resolved tenant schema for the current request using ContextVar.
- Default is None (meaning: no tenant routing applied).
- Safe across async requests.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Optional

_current_tenant_schema: ContextVar[Optional[str]] = ContextVar(
    "current_tenant_schema",
    default=None,
)


def set_current_tenant_schema(schema_name: Optional[str]) -> None:
    _current_tenant_schema.set(schema_name)


def get_current_tenant_schema() -> Optional[str]:
    return _current_tenant_schema.get()