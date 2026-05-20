# app/services/security_activity_logger.py

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session


def log_security_activity(
    db: Optional[Session],
    *,
    tenant_id: Optional[str],
    user_id: Optional[str],
    action: str,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Record a security-relevant activity.

    Minimal, startup-safe implementation:
      - Does not raise if DB is unavailable.
      - Does not block request handling.
      - Can be expanded later to write to audit_logs or a security_events table.

    Compliance intent:
      - Preserve an integration point for security auditing
      - Avoid crashing the application due to missing infra
    """
    if db is None:
        return

    # Best-effort logging only
    try:
        # If you later add a dedicated table, write here.
        # For now, this is intentionally a no-op to keep startup safe.
        _ = {
            "timestamp": datetime.utcnow(),
            "tenant_id": tenant_id,
            "user_id": user_id,
            "action": action,
            "details": details or {},
        }
    except Exception:
        return