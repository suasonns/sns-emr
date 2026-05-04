from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def log_event(
    *,
    user_id,
    role: str,
    action: str,
    entity_type: str,
    entity_id: str,
    ip: Optional[str] = None,
    db: Optional[Session] = None,
):
    """
    Audit logger.
    - Always prints (developer visibility)
    - Persists to audit_logs when db session is provided (compliance/audit readiness)
    """
    print(
        f"[AUDIT] user={user_id} role={role} action={action} "
        f"entity={entity_type}:{entity_id} ip={ip}"
    )

    if db is None:
        return

    row = AuditLog(
        user_id=str(user_id),
        role=str(role),
        action=str(action),
        entity_type=str(entity_type),
        entity_id=str(entity_id),
        created_at=datetime.utcnow(),
    )

    # Only include ip if your model has it; otherwise leave it out
    if hasattr(row, "ip") or hasattr(row, "ip_address"):
        if hasattr(row, "ip"):
            row.ip = ip
        else:
            row.ip_address = ip

    db.add(row)
    # no commit here; caller controls transaction