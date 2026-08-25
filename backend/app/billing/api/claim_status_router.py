from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.billing.security import tenant_has_automated_billing
from app.billing.audit_store import append_audit_event, build_audit_event
from app.billing.models.claim import Claim
from app.db_request_dependency import get_db_tenant_with_request_state

router = APIRouter(prefix="/billing", tags=["Billing Status Engine"])

ALLOWED_TRANSITIONS = {
    "READY": {"SENT"},
    "SENT": {"ACCEPTED", "DENIED"},
    "ACCEPTED": {"PAID", "DENIED"},
    "PAID": set(),
    "DENIED": set(),
}


@router.post("/claim-status")
def update_claim_status(
    payload: dict,
    db: Session = Depends(get_db_tenant_with_request_state),
):
    """
    Updates claim status on the real, persisted claims table and appends
    an audit event.

    Remittance visibility rule:
    - AUTOMATED tenants (NE Billing) get expanded "remittance-like" fields.
    - MANUAL tenants get status-only response (no reasons, no RA details).
    """

    patient_id = payload.get("patient_id")
    billing_cycle_id = payload.get("billing_cycle_id")
    new_status = str(payload.get("status", "")).upper().strip()
    reason = payload.get("reason")
    actor = payload.get("actor") or "dev-user"

    if not patient_id or not billing_cycle_id or not new_status:
        raise HTTPException(
            status_code=400,
            detail="patient_id, billing_cycle_id, and status are required",
        )

    claim = db.execute(
        select(Claim)
        .where(Claim.patient_id == patient_id)
        .where(Claim.billing_cycle_id == billing_cycle_id)
    ).scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    current_status = str(claim.status or "").upper()

    allowed_next = ALLOWED_TRANSITIONS.get(current_status, set())
    if new_status not in allowed_next:
        raise HTTPException(
            status_code=409,
            detail=f"Invalid transition from '{current_status}' to '{new_status}'",
        )

    # Persist status + reason on the claim row
    claim.status = new_status
    claim.last_status_reason = reason or f"Status updated to {new_status}"
    db.commit()

    # Audit event (always recorded)
    append_audit_event(
        build_audit_event(
            event_type="CLAIM_STATUS_CHANGED",
            patient_id=patient_id,
            billing_cycle_id=billing_cycle_id,
            actor=actor,
            previous_status=current_status,
            new_status=new_status,
            reason=claim.last_status_reason,
            claim_control_number=claim.claim_control_number,
            details={
                "payer_name": claim.payer_name,
                "tenant_id": str(claim.tenant_id),
            },
        )
    )

    # ---------------------------------------------------------
    # Remittance visibility gating (tenant derived from claim)
    # ---------------------------------------------------------
    tenant_id = claim.tenant_id
    automated = bool(tenant_id) and tenant_has_automated_billing(db, str(tenant_id))

    # Base response: safe for manual billers (status only)
    response = {
        "message": "Claim status updated successfully",
        "patient_id": patient_id,
        "billing_cycle_id": billing_cycle_id,
        "previous_status": current_status,
        "new_status": new_status,
    }

    # Expanded response: ONLY for AUTOMATED tenants (NE Billing)
    if automated:
        response.update(
            {
                "reason": claim.last_status_reason,
                "claim_control_number": claim.claim_control_number,
                "payer_name": claim.payer_name,
                "exported_at": claim.exported_at.isoformat() if claim.exported_at else None,
                "paid_amount": None,
                "denial_codes": None,
                "adjustments": None,
            }
        )

    return response
