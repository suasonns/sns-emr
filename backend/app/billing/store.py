from __future__ import annotations

from copy import deepcopy
from typing import Dict, List, Optional

# =========================================================
# DEV STORE (IN-MEMORY)
# Clean dev-safe shared state for billing workflow
# =========================================================

TENANTS: List[Dict] = [
    {"tenant_id": "tenant_a", "display_name": "Angela Hospice"},
    {"tenant_id": "tenant_b", "display_name": "Silva Hospice"},
]

CLAIMS: List[Dict] = [
    {
        "claim_id": "CLM-001",
        "billing_cycle_id": "CYCLE-001",
        "patient_id": "P001",
        "patient_name": "John Doe",
        "patient_mrn": "MRN001",
        "payer_name": "Medicare",
        "tenant_id": "tenant_a",
        "tenant_name": "Angela Hospice",
        "total_charge": 1200.00,
        "total_units": 10,
        "risk_score": 5,
        "status": "READY",
        "service_date": "2026-06-01",
        "claim_control_number": None,
        "exported_at": None,
        "last_status_reason": None,
    },
    {
        "claim_id": "CLM-002",
        "billing_cycle_id": "CYCLE-002",
        "patient_id": "P002",
        "patient_name": "Jane Smith",
        "patient_mrn": "MRN002",
        "payer_name": "Medicaid",
        "tenant_id": "tenant_b",
        "tenant_name": "Silva Hospice",
        "total_charge": 900.00,
        "total_units": 8,
        "risk_score": 12,
        "status": "DENIED",
        "service_date": "2026-06-02",
        "claim_control_number": None,
        "exported_at": None,
        "last_status_reason": "Initial demo denial state",
    },
]


def get_all_claims() -> List[Dict]:
    return deepcopy(CLAIMS)


def get_all_tenants() -> List[Dict]:
    return deepcopy(TENANTS)


def find_claim(patient_id: str, billing_cycle_id: str) -> Optional[Dict]:
    for claim in CLAIMS:
        if (
            claim["patient_id"] == patient_id
            and claim["billing_cycle_id"] == billing_cycle_id
        ):
            return claim
    return None


def count_lifecycle() -> Dict[str, int]:
    counts = {
        "ready": 0,
        "sent": 0,
        "accepted": 0,
        "paid": 0,
        "denied": 0,
    }

    for claim in CLAIMS:
        status = str(claim.get("status", "")).upper()
        if status == "READY":
            counts["ready"] += 1
        elif status == "SENT":
            counts["sent"] += 1
        elif status == "ACCEPTED":
            counts["accepted"] += 1
        elif status == "PAID":
            counts["paid"] += 1
        elif status == "DENIED":
            counts["denied"] += 1

    return counts