from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.billing.engine.billing_engine import BillingEngineError, generate_patient_billing
from app.billing.schemas.billing_schema import (
    BuildPatientClaimEDIRequest,
    BuildPatientClaimEDIResponse,
    BuildPatientClaimExportRequest,
    BuildPatientClaimExportResponse,
    GeneratePatientBillingRequest,
    GeneratePatientBillingResponse,
)
from app.billing.services.claim_export_service import ClaimExportError, build_patient_claim_export
from app.billing.services.edi_builder import EDIBuilderError, build_837i_text
from app.core.database import get_db

router = APIRouter(prefix="/billing", tags=["Billing"])


@router.post("/generate-patient", response_model=GeneratePatientBillingResponse)
def generate_patient(
    payload: GeneratePatientBillingRequest,
    db: Session = Depends(get_db),
):
    try:
        return generate_patient_billing(
            db=db,
            patient_id=payload.patient_id,
            billing_cycle_id=payload.billing_cycle_id,
            rate_schedule=payload.rate_schedule,
        )
    except BillingEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/export-patient-claim", response_model=BuildPatientClaimExportResponse)
def export_patient_claim(
    payload: BuildPatientClaimExportRequest,
    db: Session = Depends(get_db),
):
    try:
        return build_patient_claim_export(
            db=db,
            patient_id=payload.patient_id,
            billing_cycle_id=payload.billing_cycle_id,
        )
    except ClaimExportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/export-patient-claim-edi", response_model=BuildPatientClaimEDIResponse)
def export_patient_claim_edi(
    payload: BuildPatientClaimEDIRequest,
    db: Session = Depends(get_db),
):
    try:
        export_payload = build_patient_claim_export(
            db=db,
            patient_id=payload.patient_id,
            billing_cycle_id=payload.billing_cycle_id,
        )

        edi_text = build_837i_text(export_payload)
        claim_control_number = export_payload["claim_header"]["claim_control_number"]

        return {
            "edi_text": edi_text,
            "claim_control_number": claim_control_number,
            "billing_cycle_id": payload.billing_cycle_id,
            "patient_id": payload.patient_id,
        }
    except (ClaimExportError, EDIBuilderError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc