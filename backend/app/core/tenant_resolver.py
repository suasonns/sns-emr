"""
Tenant resolver (Phase 3.2)

ENTERPRISE GUARANTEES:
- READ-ONLY
- Queries ONLY core.tenants
- NO schema switching
- NO routing
- NO clinical table access
- SAFE to import anywhere
"""

from __future__ import annotations

from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session


def resolve_tenant_schema(
    *,
    db: Session,
    tenant_code: Optional[str],
) -> Optional[str]:
    """
    Resolve a tenant code to a PostgreSQL schema name.

    Behavior:
    - tenant_code is None or empty -> return None
    - tenant_code not found -> return None
    - tenant exists but not ACTIVE -> return None
    - tenant exists and ACTIVE -> return schema_name

    IMPORTANT:
    - This function is READ-ONLY
    - Queries ONLY core.tenants
    - Does NOT mutate session state
    """

    if not tenant_code:
        return None

    row = db.execute(
        text(
            """
            SELECT schema_name
            FROM core.tenants
            WHERE tenant_code = :tenant_code
              AND status = 'ACTIVE'
            """
        ),
        {"tenant_code": tenant_code},
    ).fetchone()

    if not row:
        return None

    return row[0]