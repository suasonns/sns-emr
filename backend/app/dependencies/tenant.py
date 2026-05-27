from __future__ import annotations

from fastapi import Request, HTTPException

# ---------------------------------------------------------------------
# ⚠️ DEPRECATED TENANT INJECTION (DO NOT USE IN RUNTIME PATHS)
# ---------------------------------------------------------------------
# This module is retained ONLY for:
#   - legacy test tooling
#   - controlled cross-tenant leak testing
#
# ✅ Enterprise runtime uses IDENTITY-BASED TENANCY ONLY:
#    - tenant comes from authenticated user (token)
#    - NOT from headers
#
# 🚫 DO NOT import this in:
#    - API routers
#    - DB dependencies
#    - production request paths
# ---------------------------------------------------------------------

ALLOWED_TENANTS = {
    "01271980-0000-0000-0000-000005101977",  # Love & Faith (REAL)
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",  # Angela Hospice
    "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",  # Silva Hospice
    "5224ceb6-e29d-4841-858e-e77f1b67fe65",  # Tenant A
    "85282f8b-fd5b-45e6-bb82-45394ef7a2f8",  # Tenant B
}


def inject_tenant(request: Request) -> str:
    """
    ❌ DEPRECATED — HEADER-BASED TENANT INJECTION

    This function is intentionally retained for:
      - legacy test harnesses
      - explicit tenant isolation testing

    ✅ SNS EMR ENTERPRISE RULE:
      - Production tenancy is derived ONLY from authenticated identity
      - This function MUST NOT be used in runtime request handling
    """

    tenant_id = request.headers.get("X-Tenant-ID")

    if not tenant_id:
        raise HTTPException(
            status_code=400,
            detail="Missing X-Tenant-ID header (deprecated path)",
        )

    if tenant_id not in ALLOWED_TENANTS:
        raise HTTPException(
            status_code=403,
            detail="Invalid tenant ID (deprecated path)",
        )

    # Attach only for test contexts
    request.state.tenant_id = tenant_id
    return tenant_id
