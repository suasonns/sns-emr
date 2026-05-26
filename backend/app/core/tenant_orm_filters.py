from __future__ import annotations

from sqlalchemy import event
from sqlalchemy.orm import Session, with_loader_criteria
from sqlalchemy.sql import false, true

from app.models.base import BaseModel


@event.listens_for(Session, "do_orm_execute")
def _tenant_filter(execute_state) -> None:
    """
    Enterprise ORM tenant filter.

    Applies tenant scoping ONLY to models that:
    - inherit from BaseModel
    - declare __tenant_scoped__ = True
    - have a tenant_id attribute
    """

    if not execute_state.is_select:
        return

    if execute_state.execution_options.get("skip_tenant_filter", False):
        return

    tenant_id = execute_state.session.info.get("tenant_id")

    execute_state.statement = execute_state.statement.options(
        with_loader_criteria(
            BaseModel,
            lambda cls: (
                cls.tenant_id == tenant_id
                if getattr(cls, "__tenant_scoped__", False)
                and hasattr(cls, "tenant_id")
                and tenant_id
                else true() if tenant_id else false()
            ),
            include_aliases=True,
            track_closure_variables=False,  # ✅ CRITICAL FIX
        )
    )


@event.listens_for(Session, "before_flush")
def _tenant_stamp_and_block(session: Session, flush_context, instances) -> None:
    """
    Auto-stamps tenant_id on new tenant-scoped objects and blocks cross-tenant writes.
    """

    if session.info.get("skip_tenant_filter", False):
        return

    tenant_id = session.info.get("tenant_id")
    if not tenant_id:
        raise RuntimeError("Tenant context missing in DB session (tenant_id not set)")

    for obj in session.new:
        if getattr(obj, "__tenant_scoped__", False) and hasattr(obj, "tenant_id"):
            existing = getattr(obj, "tenant_id", None)

            if existing is None:
                setattr(obj, "tenant_id", tenant_id)
            elif str(existing) != str(tenant_id):
                raise RuntimeError("Cross-tenant write attempt blocked")

    for obj in session.dirty:
        if getattr(obj, "__tenant_scoped__", False) and hasattr(obj, "tenant_id"):
            existing = getattr(obj, "tenant_id", None)

            if existing is not None and str(existing) != str(tenant_id):
                raise RuntimeError("Cross-tenant update attempt blocked")