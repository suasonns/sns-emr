from __future__ import annotations

import logging
import uuid

from sqlalchemy import event
from sqlalchemy.orm import Session, with_loader_criteria

from app.models.base import BaseModel
from app.core.tenant_context import get_current_tenant

logger = logging.getLogger("tenant")


# =========================================================
# UTIL
# =========================================================

def _normalize_tenant_id(value):
    if value is None:
        return None

    if isinstance(value, uuid.UUID):
        return value

    try:
        return uuid.UUID(str(value))
    except Exception:
        return None


# =========================================================
# READ FILTER (SELECT)
# =========================================================

@event.listens_for(Session, "do_orm_execute")
def _tenant_filter(execute_state) -> None:
    """
    Enterprise ORM tenant filter (GLOBAL ENFORCEMENT)

    Rules:
    - tenant_id present → enforce isolation
    - tenant_id None → SUPER ADMIN MODE
    """

    if not execute_state.is_select:
        return

    if execute_state.execution_options.get("skip_tenant_filter", False):
        return

    tenant_id = _normalize_tenant_id(get_current_tenant())

    # ✅ SUPER ADMIN MODE
    if tenant_id is None:
        logger.warning(
            "TENANT FILTER: SUPER ADMIN MODE ENABLED (no tenant filtering)"
        )
        return

    # ✅ GLOBAL FILTER (ALL TENANT MODELS)
    execute_state.statement = execute_state.statement.options(
        with_loader_criteria(
            BaseModel,
            lambda cls: (
                cls.tenant_id == tenant_id
                if getattr(cls, "__tenant_scoped__", False)
                and hasattr(cls, "tenant_id")
                else True
            ),
            include_aliases=True,
        )
    )


# =========================================================
# WRITE PROTECTION (INSERT / UPDATE / DELETE)
# =========================================================

@event.listens_for(Session, "before_flush")
def _tenant_stamp_and_block(session: Session, flush_context, instances) -> None:
    """
    Enterprise write protection

    Rules:
    - tenant_id present → enforce strict isolation
    - tenant_id None → SUPER ADMIN MODE

    Guarantees:
    - no cross-tenant writes
    - auto-stamp new records
    """

    if session.info.get("skip_tenant_filter", False):
        return

    tenant_id = _normalize_tenant_id(get_current_tenant())

    # ✅ SUPER ADMIN MODE
    if tenant_id is None:
        logger.warning(
            "TENANT WRITE: SUPER ADMIN MODE ENABLED (cross-tenant allowed)"
        )
        return

    if not tenant_id:
        raise ValueError("Tenant context missing in DB session")

    # -------------------------------------------------
    # NEW OBJECTS
    # -------------------------------------------------
    for obj in session.new:
        if getattr(obj, "__tenant_scoped__", False) and hasattr(obj, "tenant_id"):
            existing = getattr(obj, "tenant_id", None)

            if existing is None:
                setattr(obj, "tenant_id", tenant_id)
            elif str(existing) != str(tenant_id):
                raise ValueError("Cross-tenant INSERT blocked")

    # -------------------------------------------------
    # UPDATED OBJECTS
    # -------------------------------------------------
    for obj in session.dirty:
        if getattr(obj, "__tenant_scoped__", False) and hasattr(obj, "tenant_id"):
            existing = getattr(obj, "tenant_id", None)

            if existing is not None and str(existing) != str(tenant_id):
                raise ValueError("Cross-tenant UPDATE blocked")

    # -------------------------------------------------
    # DELETED OBJECTS
    # -------------------------------------------------
    for obj in session.deleted:
        if getattr(obj, "__tenant_scoped__", False) and hasattr(obj, "tenant_id"):
            existing = getattr(obj, "tenant_id", None)

            if existing is not None and str(existing) != str(tenant_id):
                raise ValueError("Cross-tenant DELETE blocked")