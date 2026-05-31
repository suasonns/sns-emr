from __future__ import annotations

import logging
import uuid

from sqlalchemy import event
from sqlalchemy.orm import Session, with_loader_criteria
from sqlalchemy.sql import false, true

from app.models.base import BaseModel

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
        return value


# =========================================================
# READ FILTER (SELECT)
# =========================================================

@event.listens_for(Session, "do_orm_execute")
def _tenant_filter(execute_state) -> None:
    """
    Enterprise ORM tenant filter.

    Behavior:
    - tenant_id = UUID → enforce tenant filtering
    - tenant_id = None → SUPER ADMIN MODE (no filtering)

    Security:
    - tenant-scoped models are protected in normal mode
    - super-admin mode explicitly bypasses filtering
    """

    if not execute_state.is_select:
        return

    if execute_state.execution_options.get("skip_tenant_filter", False):
        return

    tenant_id = _normalize_tenant_id(
        execute_state.session.info.get("tenant_id")
    )

    # ✅ SUPER ADMIN MODE — NO FILTER AT ALL
    if tenant_id is None:
        logger.warning("TENANT FILTER: SUPER ADMIN MODE ENABLED (no tenant filtering)")
        return

    execute_state.statement = execute_state.statement.options(
        with_loader_criteria(
            BaseModel,
            lambda cls: (
                cls.tenant_id == tenant_id
                if getattr(cls, "__tenant_scoped__", False)
                and hasattr(cls, "tenant_id")
                else true()
            ),
            include_aliases=True,
            track_closure_variables=False,
        )
    )


# =========================================================
# WRITE PROTECTION (INSERT / UPDATE / DELETE)
# =========================================================

@event.listens_for(Session, "before_flush")
def _tenant_stamp_and_block(session: Session, flush_context, instances) -> None:
    """
    Behavior:
    - tenant_id = UUID → enforce tenant isolation ✅
    - tenant_id = None → SUPER ADMIN MODE (no restriction)

    Enterprise Rules:
    - auto-stamp tenant_id when missing
    - prevent cross-tenant writes
    """

    if session.info.get("skip_tenant_filter", False):
        return

    tenant_id = _normalize_tenant_id(session.info.get("tenant_id"))

    # ✅ SUPER ADMIN MODE — ALLOW ALL WRITES
    if tenant_id is None:
        logger.warning("TENANT WRITE: SUPER ADMIN MODE (write allowed across tenants)")
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