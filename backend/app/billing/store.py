from __future__ import annotations

from copy import deepcopy
from typing import Dict, List

# =========================================================
# DEV STORE (IN-MEMORY)
#
# Only the demo tenant picker list remains here. Claim data now lives in
# the real, persisted `claims` table (app.billing.models.claim.Claim) --
# see app.billing.api.claim_status_router, app.billing.api.billing_queue_router,
# and app.services.dashboard_service.count_claim_lifecycle.
# =========================================================

TENANTS: List[Dict] = [
    {"tenant_id": "tenant_a", "display_name": "Angela Hospice"},
    {"tenant_id": "tenant_b", "display_name": "Silva Hospice"},
]


def get_all_tenants() -> List[Dict]:
    return deepcopy(TENANTS)