from __future__ import annotations

from fastapi import Request, HTTPException

# ✅ FIXED TENANT IDS (YOUR CONTROLLED ENVIRONMENT)
ALLOWED_TENANTS = {
    "01271980-0000-0000-0000-000005101977",  # Love & Faith (REAL)
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",  # Angela Hospice
    "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",  # Silva Hospice
    "5224ceb6-e29d-4841-858e-e77f1b67fe65",  # Tenant A
    "85282f8b-fd5b-45e6-bb82-45394ef7a2f8",  # Tenant B
}


def inject_tenant(request: Request) -> str:
    """
    Enterprise tenant enforcement (FINAL VERSION)

    ✅ No random tenants
    ✅ Only known tenant IDs allowed
    ✅ Required for every request
    ✅ Enables cross-tenant leak testing
    """

    tenant_id = request.headers.get("X-Tenant-ID")

    # ✅ Must send header
    if not tenant_id:
        raise HTTPException(
            status_code=400,
            detail="Missing X-Tenant-ID header"
        )

    # ✅ Must be one of YOUR 5 tenants
    if tenant_id not in ALLOWED_TENANTS:
        raise HTTPException(
            status_code=403,
            detail="Invalid tenant ID"
        )

    # ✅ Attach to request context
    request.state.tenant_id = tenant_id

    return tenant_id
