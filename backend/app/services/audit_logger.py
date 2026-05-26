from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


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
    Enterprise audit logger (append-only, tenant-aware, non-blocking).
    """

    print(
        f"[AUDIT] request_id={request_id} tenant={tenant_id} user={user_id} "
        f"role={role} action={action} entity={entity_type}:{entity_id} ip={ip}"
    )

    if db is None:
        return

    try:
        audit = AuditLog(
            request_id=str(request_id) if request_id else None,
            tenant_id=str(tenant_id) if tenant_id else None,
            user_id=str(user_id) if user_id else None,
            role=str(role) if role else None,
            action=str(action),
            entity_type=str(entity_type) if entity_type else None,
            entity_id=str(entity_id) if entity_id else None,
            ip_address=ip,
            created_at=datetime.utcnow(),  # ✅ CORRECT FIELD
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

        print(f"[AUDIT ERROR] {e}")
