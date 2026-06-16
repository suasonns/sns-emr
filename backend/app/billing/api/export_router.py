from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.billing.audit_store import append_audit_event, build_audit_event
from app.billing.store import find_claim
from app.db_request_dependency import get_db_tenant_with_request_state

router = APIRouter(prefix="/billing", tags=["Billing Export"])


@router.post("/export-patient-claim-edi")
def export_claim(
    payload: dict,
    db: Session = Depends(get_db_tenant_with_request_state),
):
    # db dependency is intentionally injected so request.state.db is populated
    # for middleware and future persistence.
    _ = db

    patient_id = payload.get("patient_id")
    billing_cycle_id = payload.get("billing_cycle_id")
    actor = payload.get("actor") or "dev-user"

    if not patient_id or not billing_cycle_id:
        raise HTTPException(
            status_code=400,
            detail="patient_id and billing_cycle_id are required",
        )

    claim = find_claim(
        patient_id=patient_id,
        billing_cycle_id=billing_cycle_id,
    )

    if not claim:
        raise HTTPException(
            status_code=404,
            detail="Claim not found",
        )

    current_status = str(claim.get("status", "")).upper()

    if current_status not in {"READY"}:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot export from status {current_status}",
        )

    control_number = str(uuid.uuid4())

    previous_status = current_status
    claim["status"] = "SENT"
    claim["claim_control_number"] = control_number
    claim["exported_at"] = datetime.now(timezone.utc).isoformat()
    claim["last_status_reason"] = "Claim exported to payer"

    append_audit_event(
        build_audit_event(
            event_type="CLAIM_EXPORTED",
            patient_id=patient_id,
            billing_cycle_id=billing_cycle_id,
            actor=actor,
            previous_status=previous_status,
            new_status="SENT",
            reason="Claim exported to payer",
            claim_control_number=control_number,
            details={
                "payer_name": claim.get("payer_name"),
                "tenant_id": claim.get("tenant_id"),
            },
        )
    )

    return {
        "claim_control_number": control_number,
        "edi_text": "837P SAMPLE",
        "warnings": [],
        "errors": [],
    }