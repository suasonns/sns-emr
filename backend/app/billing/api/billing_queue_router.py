from fastapi import APIRouter, Depends

from app.billing.store import get_all_claims
from app.core.security import get_current_user

router = APIRouter(prefix="/billing", tags=["Billing Queue"])


@router.get("/queue")
def get_billing_queue(
    user=Depends(get_current_user),
):
    """
    Tenant-scoped billing queue.

    - Tenant users see ONLY their own claims
    - Prevents cross-tenant billing visibility
    - NE Billing automation across tenants is handled elsewhere
    """

    claims = get_all_claims()

    return [
        claim
        for claim in claims
        if claim.get("tenant_id") == user.tenant_id
    ]