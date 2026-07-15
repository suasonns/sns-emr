"""
Tenant resolver (Phase 3.2)

ENTERPRISE GUARANTEES:
- READ-ONLY
- Queries ONLY core.tenants
- Returns BOTH tenant_id and schema_name
- NO schema switching
- NO routing
- SAFE to import anywhere
"""

from __future__ import annotations

from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


def resolve_tenant_context(
    *,
    db: Session,
    tenant_code: Optional[str],
) -> Tuple[Optional[UUID], Optional[str]]:
    """
    Resolve a tenant_code into tenant_id and schema_name.

    Returns:
        (tenant_id, schema_name)

    Behavior:
    - tenant_code is None → (None, None)
    - tenant not found → (None, None)
    - tenant not ACTIVE → (None, None)
    - tenant ACTIVE → (tenant_id, schema_name)

    IMPORTANT:
    - READ-ONLY
    - No session mutation
    """

    if not tenant_code:
        return None, None

    tenant_code = tenant_code.strip().upper()

    row = db.execute(
        text(
            """
            SELECT id, schema_name
            FROM core.tenants
            WHERE tenant_code = :tenant_code
              AND status = 'ACTIVE'
            LIMIT 1
            """
        ),
        {"tenant_code": tenant_code},
    ).fetchone()

    if not row:
        return None, None

    tenant_id, schema_name = row

    # ✅ DEFENSIVE VALIDATION
    if not schema_name:
        return None, None

    return tenant_id, schema_name