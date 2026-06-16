from __future__ import annotations

from datetime import datetime
from uuid import uuid4


class CoverageAuditError(Exception):
    """Raised when coverage audit logging fails."""
    pass


def log_coverage_audit(
    *,
    db=None,
    tenant_id: str | None = None,
    action: str = "COVERAGE_AUDIT",
    entity_type: str | None = None,
    entity_id: str | None = None,
    user_id: str | None = None,
    role: str | None = None,
    request_id: str | None = None,
    ip_address: str | None = None,
    metadata: dict | None = None,
):
    """
    ✅ ENTERPRISE-SAFE COVERAGE AUDIT LOGGER

    Current behavior:
    - Non-blocking console/log fallback
    - Signature matches billing engine usage
    - Easy to upgrade later to DB-backed audit writes
    """

    try:
        log_entry = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "tenant_id": tenant_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "user_id": user_id,
            "role": role,
            "request_id": request_id,
            "ip_address": ip_address,
            "metadata": metadata or {},
        }

        print("COVERAGE AUDIT:", log_entry)

        # Future DB-backed version can go here:
        # if db:
        #     db.execute(...)
        #     db.commit()

    except Exception as exc:
        raise CoverageAuditError(f"Failed to log coverage audit: {exc}") from exc