from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db  # adjust if needed
from app.core.security import get_current_user
from app.core.patient_access import get_authorized_patient
from app.schemas.translation import (
    RNRecertDraftCreate,
    RNRecertDraftRead,
    RNRecertFinalizeRequest,
    TranslationRealtimeRequest,
    TranslationRealtimeResponse,
)
from app.services.translation_engine import run_realtime_translation
from app.models.rn_recert_assessment import RNRecertAssessment

router = APIRouter()


@router.post("/clinical-translation/realtime", response_model=TranslationRealtimeResponse)
def clinical_translation_realtime(
    payload: TranslationRealtimeRequest,
) -> TranslationRealtimeResponse:
    return run_realtime_translation(payload.observations)


@router.post("/rn-recert/draft", response_model=RNRecertDraftRead)
def create_rn_recert_draft(
    payload: RNRecertDraftCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        patient_uuid = uuid.UUID(str(payload.patient_id))
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="patient_id must be a valid UUID") from None

    patient = get_authorized_patient(db, patient_uuid, current_user)

    obj = RNRecertAssessment(
        patient_id=payload.patient_id,
        tenant_id=getattr(patient, "tenant_id", None),
        benefit_period_id=payload.benefit_period_id,
        created_by_user_id=payload.created_by_user_id,
        pps_score=payload.pps_score,
        kps_score=payload.kps_score,
        fast_stage=payload.fast_stage,
        nyha_class=payload.nyha_class,
        adl_level=payload.adl_level,
        adl_dependency_count=payload.adl_dependency_count,
        primary_diagnosis=payload.primary_diagnosis,
        eligibility_recommendation=payload.eligibility_recommendation.value,
        raw_observations_json=payload.raw_observations_json,
        clarification_items_json=payload.clarification_items_json,
        normalized_observations_json=payload.normalized_observations_json,
        translation_output_json=payload.translation_output_json,
        translation_source_map_json=payload.translation_source_map_json,
        interpretation_output_json=payload.interpretation_output_json,
        translation_mode_used=payload.translation_mode_used.value,
        status="DRAFT",
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/rn-recert/{assessment_id}/finalize", response_model=RNRecertDraftRead)
def finalize_rn_recert(
    assessment_id: str,
    payload: RNRecertFinalizeRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        assessment_uuid = uuid.UUID(str(assessment_id))
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="assessment_id must be a valid UUID") from None

    obj = db.query(RNRecertAssessment).filter(RNRecertAssessment.id == assessment_uuid).first()
    if not obj:
        raise HTTPException(status_code=404, detail="RN recert assessment not found")

    # Tenant/care-team scoping: only staff authorized for this patient may finalize.
    get_authorized_patient(db, obj.patient_id, current_user)

    # deterministic finalize validation
    if not any([obj.pps_score, obj.kps_score, obj.fast_stage, obj.nyha_class]):
        raise HTTPException(status_code=422, detail="Missing required score path (PPS/KPS/FAST/NYHA)")
    if obj.adl_dependency_count is None:
        raise HTTPException(status_code=422, detail="Missing ADL dependency count")
    interpretation = obj.interpretation_output_json or {}
    if not any([
        interpretation.get("functional_decline"),
        interpretation.get("nutritional_decline"),
        interpretation.get("clinical_decline"),
    ]):
        raise HTTPException(status_code=422, detail="Missing decline evidence")
    if not payload.translation_accepted:
        raise HTTPException(status_code=422, detail="Translation must be accepted before finalize")

    from datetime import datetime

    # Reviewer identity is taken from the authenticated session, not the
    # client-supplied payload, to prevent callers from attributing the
    # finalize action to an arbitrary user id.
    obj.translation_reviewed_by = current_user.id
    obj.translation_reviewed_at = datetime.utcnow()
    obj.translation_accepted = True
    obj.status = "FINAL"
    obj.finalized_at = datetime.utcnow()

    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj