"""Agency (tenant) profile — read-only, tenant-scoped.

Backs the "General" tab of Agency Settings with the real identity fields
that exist on the `tenants` table. Per this project's "never fabricate
data" policy, only columns that actually exist are returned; the frontend
must not invent address/phone/administrator/service-area/operating-hours
values that have no backing schema.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.patients import get_db_with_request_state, require_tenant_user, _tenant_id_uuid
from app.models.tenant import Tenant

router = APIRouter(prefix="/agency-profile", tags=["agency-profile"])


@router.get("")
def get_agency_profile(
    db=Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        return None
    return {
        "tenant_id": str(tenant.id),
        "legal_name": tenant.legal_name,
        "display_name": tenant.display_name,
        "npi": tenant.npi,
        "ein": tenant.ein,
        "ptan": tenant.ptan,
        "tenant_type": tenant.tenant_type,
        "status": tenant.status,
        "cbsa_code": tenant.cbsa_code,
    }
