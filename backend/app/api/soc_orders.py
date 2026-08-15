from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db_tenant_dependency import get_db_tenant
from app.models.patient import Patient
from app.models.admission import Admission
from app.tenancy.registry import assert_known_tenant

# ✅ CRITICAL SERVICES
from app.services.admission_authorization_service import authorize_admission
from app.services.admission_guardrails_service import AdmissionGuardrailsService

router = APIRouter(prefix="/soc-orders", tags=["soc-orders"])


# =========================================================
# REQUEST MODEL
# =========================================================

class RNAdmissionOrder(BaseModel):
    order_rn: bool = True

    # ✅ REQUIRED for guardrails
    narrative: str | None = None
    has_decline: bool | None = None
    lcd_status: str | None = None


# =========================================================
# TENANT ENFORCEMENT
# =========================================================

def _require_tenant(user) -> str:
    tenant_id = getattr(user, "tenant_id", None)
    if tenant_id is None and isinstance(user, dict):
        tenant_id = user.get("tenant_id")

    if not tenant_id:
        raise HTTPException(status_code=401, detail="Missing tenant context")

    assert_known_tenant(str(tenant_id))
    return str(tenant_id)


# =========================================================
# MAIN ENDPOINT
# =========================================================

@router.post(
    "/patients/{patient_id}/rn-admission",
    summary="Finalize RN admission order and create ICA tasks",
)
def finalize_rn_admission_order(
    patient_id: uuid.UUID,
    payload: RNAdmissionOrder,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    tenant_id = _require_tenant(user)

    # -----------------------------------------------------
    # LOAD PATIENT
    # -----------------------------------------------------

    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id, Patient.tenant_id == tenant_id)
        .first()
    )

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    if not payload.order_rn:
        raise HTTPException(status_code=400, detail="RN admission order is required")

    now = datetime.now(timezone.utc)

    # -----------------------------------------------------
    # ✅ GUARDRAILS (ENTERPRISE ENFORCEMENT)
    # -----------------------------------------------------

    guardrail_result = AdmissionGuardrailsService.assess_admission(
        db=db,
        admission={"id": None},
        tenant_id=tenant_id,
        patient_id=str(patient.id),
        user_id=str(getattr(user, "id", "")),
        narrative_text=payload.narrative,
        has_measurable_decline=payload.has_decline,
        lcd_status=payload.lcd_status,
        flush=True,
    )

    # 🚨 HARD STOP
    if guardrail_result.get("hard_stop", False):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "ADMISSION_BLOCKED_BY_GUARDRAILS",
                "message": "Admission blocked due to clinical documentation risk.",
                "severity": guardrail_result["severity"],
                "flags": guardrail_result["flags"],
                "requires_md_review": guardrail_result["requires_md_review"],
                "rn_explanation": guardrail_result["rn_explanation"],
            },
        )

    # -----------------------------------------------------
    # ✅ ADMISSION AUTHORIZATION (CORRECT SERVICE)
    # -----------------------------------------------------

    latest_admission = (
        db.query(Admission)
        .filter(Admission.patient_id == patient.id)
        .order_by(Admission.created_at.desc())
        .first()
    )
    
    election_signed_at = (
        latest_admission.election_signed_at
        if latest_admission
        else None
    )

    if not election_signed_at:
        raise HTTPException(
            status_code=400,
            detail="election_signed_at must be set before admission authorization.",
        )

    try:
        authorize_admission(
            db=db,
            patient_id=patient.id,
            election_signed_at=election_signed_at,
            authorized_by_user_id=getattr(user, "id", None),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Admission authorization failed: {str(e)}",
        )

    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return {
        "status": "rn_admission_finalized",
        "patient_id": str(patient_id),
        "guardrails": guardrail_result,
    }