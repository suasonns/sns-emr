from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def audit_event(
    *,
    db: Session,
    action: str,
    entity_type: str,
    entity_id: str,
    user_id: Optional[str] = None,
    role: Optional[str] = None,
    ip_address: Optional[str] = None,
    tenant_id: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Enterprise-safe audit logger.

    Goal:
      - Never crash business endpoints due to audit schema drift.
      - Write only columns that exist on the AuditLog model.
      - Ignore fields not present (tenant_id/meta/etc.) safely.
    """

    # Discover model columns to avoid invalid keyword arguments
    model_cols = set(getattr(AuditLog, "__table__").columns.keys())

    data: Dict[str, Any] = {}
    if "user_id" in model_cols:
        data["user_id"] = str(user_id) if user_id else ""
    if "role" in model_cols:
        data["role"] = str(role or "")
    if "action" in model_cols:
        data["action"] = action
    if "entity_type" in model_cols:
        data["entity_type"] = entity_type
    if "entity_id" in model_cols:
        data["entity_id"] = entity_id
    if "ip_address" in model_cols:
        data["ip_address"] = ip_address

    # If your AuditLog table/model ever adds these later, this will auto-start writing them:
    if tenant_id is not None and "tenant_id" in model_cols:
        data["tenant_id"] = tenant_id
    if meta is not None and "meta" in model_cols:
        data["meta"] = meta

    # created_at is usually present; if not, DB default handles it
    if "created_at" in model_cols:
        data["created_at"] = datetime.now(timezone.utc)

    try:
        db.add(AuditLog(**data))
    except Exception:
        # Never let audit failure crash the clinical workflow
        return