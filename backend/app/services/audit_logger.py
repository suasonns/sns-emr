from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog

logger = logging.getLogger("audit")


# =========================================================
# ✅ TIME HELPER (CONSISTENT UTC)
# =========================================================
def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# =========================================================
# MAIN LOGGER
# =========================================================
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

    Guarantees:
    - Append-only
    - NEVER blocks clinical workflows
    - Tenant context enforced
    - Uses SAVEPOINT to isolate audit writes
    """

    # ---------------------------------------------------------
    # Resolve tenant + user context
    # ---------------------------------------------------------
    if db is not None:
        tenant_id = tenant_id or db.info.get("tenant_id")
        user_id = user_id or db.info.get("user_id")

    # ---------------------------------------------------------
    # Console logging (always safe)
    # ---------------------------------------------------------
    if tenant_id:
        logger.info(
            "[AUDIT] tenant=%s user=%s role=%s action=%s entity=%s:%s",
            tenant_id,
            user_id,
            role,
            action,
            entity_type,
            entity_id,
        )
    else:
        logger.warning(
            "[AUDIT] tenant=None action=%s entity=%s:%s (skipped DB write)",
            action,
            entity_type,
            entity_id,
        )

    # ---------------------------------------------------------
    # DB write (NON-BLOCKING)
    # ---------------------------------------------------------
    if db is None or tenant_id is None:
        return

    now = _utcnow()

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
            # NOTE: the mapped attribute is `event_metadata` (DB column
            # "metadata"); `AuditLog.metadata` is SQLAlchemy's reserved
            # declarative MetaData descriptor. Passing metadata=... here
            # previously set a throwaway plain instance attribute that
            # shadowed that descriptor and was never persisted -- every
            # caller's metadata silently vanished. Fixed to write the
            # actual mapped column.
            event_metadata=metadata or {},           # ✅ prevent None
            created_at=now,                          # ✅ timezone-aware
            updated_at=now,                          # ✅ REQUIRED COLUMN FIX
            created_by=str(user_id) if user_id else None,
        )

        # ✅ SAVEPOINT (critical)
        with db.begin_nested():
            db.add(audit)
            db.flush()

        # commit only if standalone
        if commit:
            db.commit()

    except Exception as e:
        # ✅ NEVER break clinical flow
        logger.exception("Audit log write failed (ignored): %s", e)
        return