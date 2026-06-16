from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user

from app.billing.security import require_automated_billing
from app.billing.engine.billing_engine import (
    BillingEngineError,
    generate_patient_billing,
)
from app.billing.services.claim_export_service import (
    ClaimExportError,
    build_patient_claim_export,
)
from app.billing.services.edi_builder import (
    EDIBuilderError,
    build_837i_text,
    save_edi_to_file,
)
from app.billing.schemas.billing_schema import (
    GeneratePatientBillingRequest,
    GeneratePatientBillingResponse,
    BuildPatientClaimExportRequest,
    BuildPatientClaimExportResponse,
    BuildPatientClaimEDIRequest,
    BuildPatientClaimEDIResponse,
)
from app.billing.validators.claim_validator import validate_claim
from app.billing.models.claim_export_log import ClaimExportLog


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(prefix="/billing", tags=["Billing"])


# =========================================================
# BILLING GENERATION (AUTOMATED ONLY)
# =========================================================

@router.post(
    "/generate-patient",
    response_model=GeneratePatientBillingResponse,
)
def generate_patient(
    payload: GeneratePatientBillingRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_automated_billing(db, str(user.tenant_id))

    try:
        return generate_patient_billing(
            db=db,
            patient_id=payload.patient_id,
            billing_cycle_id=payload.billing_cycle_id,
            rate_schedule=payload.rate_schedule,
        )
    except BillingEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# =========================================================
# CLAIM EXPORT (AUTOMATED ONLY)
# =========================================================

@router.post(
    "/export-patient-claim",
    response_model=BuildPatientClaimExportResponse,
)
def export_patient_claim(
    payload: BuildPatientClaimExportRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_automated_billing(db, str(user.tenant_id))

    try:
        return build_patient_claim_export(
            db=db,
            patient_id=payload.patient_id,
            billing_cycle_id=payload.billing_cycle_id,
        )
    except ClaimExportError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# =========================================================
# EDI EXPORT (AUTOMATED ONLY)
# =========================================================

@router.post(
    "/export-patient-claim-edi",
    response_model=BuildPatientClaimEDIResponse,
)
def export_patient_claim_edi(
    payload: BuildPatientClaimEDIRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_automated_billing(db, str(user.tenant_id))

    try:
        export_payload = build_patient_claim_export(
            db=db,
            patient_id=payload.patient_id,
            billing_cycle_id=payload.billing_cycle_id,
        )

        validation = validate_claim(export_payload)
        errors = validation.get("errors", [])
        warnings = validation.get("warnings", [])

        if errors and not payload.override_used:
            raise HTTPException(status_code=400, detail=errors)

        edi_text = build_837i_text(export_payload)

        file_path = save_edi_to_file(
            db=db,
            edi_text=edi_text,
            export_payload=export_payload,
        )

        log = ClaimExportLog(
            id=str(uuid4()),
            patient_id=payload.patient_id,
            billing_cycle_id=payload.billing_cycle_id,
            file_path=file_path,
            override_used=payload.override_used,
            override_reason=payload.override_reason,
        )

        db.add(log)
        db.commit()

        return {
            "edi_text": edi_text,
            "file_path": file_path,
            "errors": errors,
            "warnings": warnings,
        }

    except (ClaimExportError, EDIBuilderError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))