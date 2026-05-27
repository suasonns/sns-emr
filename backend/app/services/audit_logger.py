from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog

logger = logging.getLogger("audit")


def log_event(
    *,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    role: Optional[str] = None,
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    ip: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None,
    commit: bool = True,
) -> None:
    """
    Enterprise audit logger.

    Rules:
    - Append-only
    - Never blocks request execution
    - Tenant context MUST be present (except explicit system/bootstrap events)
    """

    # ---------------------------------------------------------
    # Resolve tenant + user context from DB session if omitted
    # ---------------------------------------------------------
    if db is not None:
        # SQLAlchemy Session.info is the canonical place for request context
        tenant_id = tenant_id or db.info.get("tenant_id")
        user_id = user_id or db.info.get("user_id")

    # ---------------------------------------------------------
    # Console log (human-readable, dev-friendly)
    # ---------------------------------------------------------
    note = metadata.get("note") if isinstance(metadata, dict) else None

    if tenant_id is None:
        if note:
            logger.info(
                "[AUDIT] tenant=None (expected) action=%s entity=%s:%s note=%s",
                action,
                entity_type,
                entity_id,
                note,
            )
        else:
            logger.error(
                "[AUDIT ERROR] Tenant context missing in DB session (tenant_id not set)"
            )
    else:
        logger.info(
            "[AUDIT] tenant=%s user=%s role=%s action=%s entity=%s:%s",
            tenant_id,
            user_id,
            role,
            action,
            entity_type,
            entity_id,
        )

    # ---------------------------------------------------------
    # DB persistence (never blocks request)
    # ---------------------------------------------------------
    if db is None:
        return

    if tenant_id is None:
        # Never write audit rows without tenant context
        return

    try:
        audit = AuditLog(
            request_id=str(request_id) if request_id else None,
            tenant_id=str(tenant_id),
            user_id=str(user_id) if user_id else None,
            role=str(role) if role else None,
            action=str(action),
            entity_type=str(entity_type) if entity_type else None,
            entity_id=str(entity_id) if entity_id else None,
            ip_address=ip,
            metadata=metadata,
            created_at=datetime.utcnow(),
        )

        db.add(audit)
        db.flush()

        if commit:
            db.commit()

    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass

        # Audit failures must never break the app
        logger.exception("Audit log write failed: %s", e)