# app/api/f2f.py

"""
Face-to-Face (F2F) encounter endpoints per docs/compliance/f2f.md.

F2F is a separate ENCOUNTER workflow from CTI CERTIFICATION
(app/api/certifications.py) — performer/signing authority is never
combined or inferred between the two. An NP who performs/signs an F2F
gains ZERO CTI certification authority.

Additive-only lifecycle: DRAFT -> FINALIZED. Only F2F_PERFORMER_ROLES
(Hospice Physician / Medical Director / Medical Director Designee /
Attending Physician / hospice-employed or contracted NP / hospice-employed
or contracted PA) may create a draft (the performer records their own
encounter) or finalize it. Any clinical role may list/view F2F encounters
and their status history. `performed_by_role`/attestor role is ALWAYS the
endpoint-authenticated user's own role — never accepted from request
body.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.patient_access import get_authorized_patient
from app.core.security import CurrentUser
from app.core.database import get_db
from app.core.permissions import require_roles
from app.models.benefit_period import BenefitPeriod
from app.models.f2f_encounter import F2FEncounter
from app.models.user import User
from app.schemas.f2f import (
    F2FCreateRequest,
    F2FCreateResponse,
    F2FFinalizeRequest,
    F2FFinalizeResponse,
)
from app.services import f2f_service as svc
from app.services import clinical_reasoning_bridge
from app.services.audit_logger import log_event

router = APIRouter(prefix="/f2f", tags=["F2F"])

# Any clinical role may list/view F2F encounters and their status
# history; only F2F_PERFORMER_ROLES (physician-level + NP + PA) may
# create a draft or finalize an encounter — see require_roles(...) below.
CLINICAL_ROLES = ["LVN", "RN", "NP", "PA", "MD", "MEDICAL_DIRECTOR", "ATTENDING_PHYSICIAN", "HOSPICE_PHYSICIAN"]

# Request/response schemas moved to app/schemas/f2f.py (2026-08-22) — this
# was previously an inline duplicate of a stale, unused schema module.
# See app/schemas/f2f.py for the authoritative contract.


# =========================================================
# HELPERS
# =========================================================

def _user_name_map(db: Session, user_ids: set) -> dict:
    ids = {uid for uid in user_ids if uid}
    if not ids:
        return {}
    rows = db.query(User.id, User.full_name, User.display_name).filter(User.id.in_(ids)).all()
    return {row[0]: (row[2] or row[1] or "Unknown") for row in rows}


def _generate_f2f_summary(f2f: F2FEncounter) -> str:
    parts: list[str] = []

    parts.append(
        f"Face-to-face encounter performed on {f2f.encounter_date} for continued hospice eligibility review."
    )

    if f2f.primary_diagnosis:
        parts.append(f"Primary diagnosis: {f2f.primary_diagnosis}.")

    if f2f.secondary_conditions:
        parts.append(f"Secondary conditions: {f2f.secondary_conditions}.")

    if f2f.kps_score is not None:
        parts.append(f"KPS score is {f2f.kps_score}%.")

    if f2f.pps_score_previous is not None and f2f.pps_score_current is not None:
        parts.append(
            f"PPS declined from {f2f.pps_score_previous}% to {f2f.pps_score_current}%."
        )
    elif f2f.pps_score_current is not None:
        parts.append(f"PPS score is {f2f.pps_score_current}%.")

    if f2f.ecog_score_previous is not None and f2f.ecog_score_current is not None:
        if f2f.ecog_score_current > f2f.ecog_score_previous:
            parts.append(
                f"ECOG performance status worsened from {f2f.ecog_score_previous} to {f2f.ecog_score_current}."
            )
        else:
            parts.append(
                f"ECOG performance status is {f2f.ecog_score_current} (previously {f2f.ecog_score_previous})."
            )
    elif f2f.ecog_score_current is not None:
        parts.append(f"ECOG performance status is {f2f.ecog_score_current}.")

    if f2f.fast_score:
        parts.append(f"FAST stage is {f2f.fast_score}.")

    if f2f.nyha_class:
        parts.append(f"NYHA class is {f2f.nyha_class}.")

    if f2f.adl_dependency_level:
        if f2f.adl_dependency_count is not None:
            parts.append(
                f"Patient requires {f2f.adl_dependency_level} assistance in {f2f.adl_dependency_count} ADLs."
            )
        else:
            parts.append(
                f"Patient requires {f2f.adl_dependency_level} assistance with ADLs."
            )

    if f2f.is_bedbound:
        parts.append("Patient is predominantly bedbound.")

    if f2f.weight_loss_lbs is not None:
        parts.append(f"Documented weight loss of {f2f.weight_loss_lbs} lbs.")

    if f2f.oral_intake_decline:
        parts.append("Oral intake has declined.")

    if f2f.dysphagia:
        parts.append("Dysphagia is present.")

    if f2f.hospitalizations_30d is not None:
        parts.append(
            f"{f2f.hospitalizations_30d} hospitalizations in the past 30 days."
        )

    if (
        f2f.oxygen_lpm_previous is not None
        and f2f.oxygen_lpm_current is not None
    ):
        parts.append(
            f"Oxygen requirement increased from {f2f.oxygen_lpm_previous}L to {f2f.oxygen_lpm_current}L."
        )
    elif f2f.oxygen_lpm_current is not None:
        parts.append(f"Current oxygen requirement is {f2f.oxygen_lpm_current}L.")

    if f2f.clinical_decline_summary:
        parts.append(f2f.clinical_decline_summary.strip())

    parts.append(
        "Clinical findings support progression of terminal disease and continued hospice eligibility."
    )

    return " ".join(parts)


def _extract_f2f_reasoning_payload(f2f: F2FEncounter) -> dict:
    """
    Bridges an F2FEncounter's structured decline fields into the flat
    assessment_data dict the shared ClinicalReasoningEngine expects, so
    MD/NP F2F decline evidence (PPS, ECOG, ADL dependency, oxygen
    requirement, hospitalizations, dysphagia, weight loss) feeds the same
    shared findings / clinical_reasoning_results / IDG intelligence
    stream as RN/LVN and MSW/SC.
    """
    payload: dict = {
        "source": "F2F",
        "pps_score_current": f2f.pps_score_current,
        "pps_score_previous": f2f.pps_score_previous,
        "ecog_score_current": f2f.ecog_score_current,
        "ecog_score_previous": f2f.ecog_score_previous,
        "oxygen_lpm_current": f2f.oxygen_lpm_current,
        "oxygen_lpm_previous": f2f.oxygen_lpm_previous,
        "is_bedbound": f2f.is_bedbound,
        "adl_dependency_level": f2f.adl_dependency_level,
        "hospitalizations_30d": f2f.hospitalizations_30d,
        "dysphagia": f2f.dysphagia,
        "weight_loss_lbs": f2f.weight_loss_lbs,
        "clinical_decline_summary": f2f.clinical_decline_summary,
        "terminal_diagnosis": f2f.primary_diagnosis,
    }
    return {key: value for key, value in payload.items() if value not in (None, "")}


def _validate_f2f_for_finalize(f2f: F2FEncounter) -> None:
    errors: list[str] = []

    # At least one scoring system required
    if not any([
        f2f.kps_score is not None,
        f2f.pps_score_current is not None,
        f2f.ecog_score_current is not None,
        bool(f2f.fast_score),
        bool(f2f.nyha_class),
    ]):
        errors.append("At least one scoring system is required (KPS, PPS, ECOG, FAST, or NYHA).")

    # ADL dependency required
    if not f2f.adl_dependency_level:
        errors.append("ADL dependency level is required.")

    # At least one objective decline indicator required
    if not any([
        f2f.weight_loss_lbs is not None,
        f2f.hospitalizations_30d is not None,
        f2f.oxygen_lpm_current is not None,
        f2f.is_bedbound is True,
        f2f.oral_intake_decline is True,
        f2f.dysphagia is True,
    ]):
        errors.append("At least one objective decline indicator is required.")

    # Narrative must be individualized enough to support ADR
    if not f2f.summary or len(f2f.summary.strip()) < 200:
        errors.append("Narrative summary is insufficient for ADR support.")

    if errors:
        raise HTTPException(status_code=422, detail=errors)


def _serialize(f2f: F2FEncounter, name_map: dict | None = None) -> dict:
    name_map = name_map or {}
    return {
        "id": str(f2f.id),
        "patient_id": str(f2f.patient_id),
        "benefit_period_id": str(f2f.benefit_period_id),
        "status": f2f.status,
        "status_label": svc.label_for(f2f.status),
        "encounter_date": f2f.encounter_date.isoformat() if f2f.encounter_date else None,
        "performed_by_role": f2f.performed_by_role,
        "performed_by_user_id": str(f2f.performed_by_user_id) if f2f.performed_by_user_id else None,
        "performed_by_name": name_map.get(f2f.performed_by_user_id),
        "attesting_provider_user_id": str(f2f.attesting_provider_user_id) if f2f.attesting_provider_user_id else None,
        "attesting_provider_name": name_map.get(f2f.attesting_provider_user_id),
        "attested_at": f2f.attested_at.isoformat() if f2f.attested_at else None,
        "summary": f2f.summary,
        "finalized_at": f2f.finalized_at.isoformat() if f2f.finalized_at else None,
    }


def _get_f2f_or_404(db: Session, f2f_id: UUID, user: CurrentUser) -> F2FEncounter:
    f2f = svc.get_f2f_encounter(db, tenant_id=user.tenant_id, f2f_encounter_id=f2f_id)
    if not f2f:
        raise HTTPException(status_code=404, detail="F2F encounter not found.")
    get_authorized_patient(db, f2f.patient_id, user)
    return f2f


# =========================================================
# LIST / STATUS HISTORY
# =========================================================

@router.get("/patients/{patient_id}", summary="List a patient's F2F encounters")
def list_f2f_encounters(
    patient_id: UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    get_authorized_patient(db, patient_id, user)
    encounters = svc.list_f2f_encounters(db, tenant_id=user.tenant_id, patient_id=patient_id)
    ids = set()
    for e in encounters:
        ids.update({e.performed_by_user_id, e.attesting_provider_user_id})
    name_map = _user_name_map(db, ids)
    return [_serialize(e, name_map) for e in encounters]


@router.get("/{f2f_id}/status-history", summary="Immutable status-transition audit trail for an F2F encounter")
def f2f_status_history(
    f2f_id: UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    f2f = _get_f2f_or_404(db, f2f_id, user)
    events = svc.get_status_history(db, tenant_id=user.tenant_id, f2f_encounter_id=f2f.id)
    ids = {e.changed_by_user_id for e in events if e.changed_by_user_id}
    name_map = _user_name_map(db, ids)
    return [
        {
            "id": str(e.id),
            "from_status": e.from_status,
            "from_status_label": svc.label_for(e.from_status) if e.from_status else None,
            "to_status": e.to_status,
            "to_status_label": svc.label_for(e.to_status),
            "changed_by_user_id": str(e.changed_by_user_id) if e.changed_by_user_id else None,
            "changed_by_name": name_map.get(e.changed_by_user_id),
            "changed_by_role": e.changed_by_role,
            "changed_at": e.changed_at.isoformat() if e.changed_at else None,
            "reason": e.reason,
            "automatic": e.automatic,
            "evidence": e.evidence,
        }
        for e in events
    ]


# =========================================================
# CREATE F2F (DRAFT)
# =========================================================

@router.post("/", response_model=F2FCreateResponse)
def create_f2f_endpoint(
    request: F2FCreateRequest,
    db: Session = Depends(get_db),
    # Only the actual performer/signer roles may be recorded as the F2F
    # performer. RN/LVN/PA(disabled-by-default)/Administrator/DPCS may
    # never create a draft claiming to have performed the encounter —
    # allow_clinical_admin=False so administrative rank never satisfies
    # this gate.
    user: CurrentUser = Depends(require_roles(svc.F2F_PERFORMER_ROLES, allow_clinical_admin=False)),
):
    get_authorized_patient(db, request.patient_id, user)

    # Validate benefit period ownership + encounter date
    bp = (
        db.query(BenefitPeriod)
        .filter(
            BenefitPeriod.id == request.benefit_period_id,
            BenefitPeriod.patient_id == request.patient_id,
            BenefitPeriod.tenant_id == user.tenant_id,
            BenefitPeriod.is_current == True,
        )
        .first()
    )

    if not bp:
        raise HTTPException(status_code=422, detail="Invalid or inactive benefit period.")

    if request.encounter_date < bp.start_date:
        raise HTTPException(
            status_code=422,
            detail="Encounter date is before the benefit period start date.",
        )

    if bp.end_date is not None and request.encounter_date > bp.end_date:
        raise HTTPException(
            status_code=422,
            detail="Encounter date is after the benefit period end date.",
        )

    # Create draft through service — performed_by_role is ALWAYS the
    # authenticated user's own role, never the request body value.
    try:
        f2f = svc.create_f2f(
            db=db,
            tenant_id=user.tenant_id,
            patient_id=request.patient_id,
            benefit_period_id=request.benefit_period_id,
            encounter_date=request.encounter_date,
            performed_by_role=user.role,
            performed_by_user_id=user.user_id,
            summary=request.summary,
            created_by=user.user_id,
            created_by_role=user.role,
        )
    except svc.F2FError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    # Persist structured data
    f2f.kps_score = request.kps_score
    f2f.pps_score_previous = request.pps_score_previous
    f2f.pps_score_current = request.pps_score_current
    f2f.ecog_score_previous = request.ecog_score_previous
    f2f.ecog_score_current = request.ecog_score_current
    f2f.fast_score = request.fast_score
    f2f.nyha_class = request.nyha_class
    f2f.adl_dependency_level = request.adl_dependency_level
    f2f.adl_dependency_count = request.adl_dependency_count
    f2f.is_bedbound = request.is_bedbound
    f2f.weight_loss_lbs = request.weight_loss_lbs
    f2f.oral_intake_decline = request.oral_intake_decline
    f2f.dysphagia = request.dysphagia
    f2f.hospitalizations_30d = request.hospitalizations_30d
    f2f.oxygen_lpm_previous = request.oxygen_lpm_previous
    f2f.oxygen_lpm_current = request.oxygen_lpm_current
    f2f.primary_diagnosis = request.primary_diagnosis
    f2f.secondary_conditions = request.secondary_conditions
    f2f.clinical_decline_summary = request.clinical_decline_summary

    # Auto-generate individualized summary if empty
    if not f2f.summary:
        f2f.summary = _generate_f2f_summary(f2f)

    log_event(
        db=db, tenant_id=str(user.tenant_id), user_id=user.user_id, role=user.role,
        action="CREATE_F2F_DRAFT", entity_type="f2f_encounter", entity_id=str(f2f.id),
        metadata={"patient_id": str(request.patient_id), "performed_by_role": f2f.performed_by_role},
    )
    db.commit()
    db.refresh(f2f)

    return F2FCreateResponse(
        id=f2f.id,
        status=f2f.status,
        encounter_date=f2f.encounter_date,
    )


# =========================================================
# FINALIZE F2F
# =========================================================

@router.post("/{f2f_id}/finalize", response_model=F2FFinalizeResponse)
def finalize_f2f_endpoint(
    f2f_id: UUID,
    request: F2FFinalizeRequest,
    db: Session = Depends(get_db),
    # Only F2F performer-tier roles may finalize — Administrator/DPCS are
    # oversight/monitoring roles only and must never gain finalize
    # capability merely by having visibility into the F2F queue.
    user: CurrentUser = Depends(require_roles(svc.F2F_PERFORMER_ROLES, allow_clinical_admin=False)),
):
    f2f = _get_f2f_or_404(db, f2f_id, user)

    if not f2f.summary:
        f2f.summary = _generate_f2f_summary(f2f)

    # ADR / CMS-oriented validation
    _validate_f2f_for_finalize(f2f)

    # NP or PA performed F2F -> capture physician review/attestation on
    # the encounter. The attesting role MUST be a genuine physician-level
    # role (never Administrator/DPCS) and is ALWAYS the authenticated
    # caller's own role, never accepted from the request body.
    if f2f.performed_by_role in ("NP", "PA"):
        if not svc.is_authorized_f2f_physician_attestor(user.role):
            raise HTTPException(
                status_code=403,
                detail="Physician-level review (Medical Director/Attending Physician/Hospice Physician) "
                f"is required to finalize an {f2f.performed_by_role}-performed F2F.",
            )

        if not request.attestation_summary:
            raise HTTPException(
                status_code=422,
                detail=f"Attestation summary is required for {f2f.performed_by_role}-performed F2F.",
            )

        f2f.attesting_provider_user_id = user.user_id
        f2f.attested_at = datetime.now(timezone.utc)

    # Finalize through service — finalized_by_role is ALWAYS the
    # authenticated user's own role, never the request body.
    try:
        f2f = svc.finalize_f2f(db=db, f2f=f2f, finalized_by=user.user_id, finalized_by_role=user.role)
    except svc.F2FError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    # Feed the F2F's decline evidence into the shared Clinical Reasoning
    # Engine -- same findings / clinical_reasoning_results / IDG
    # Intelligence stream as RN/LVN visit finalize and MSW/SC ICA lock,
    # so the whole care team has one source of clinical intelligence.
    clinical_reasoning_bridge.run_clinical_reasoning(
        db=db,
        patient_id=f2f.patient_id,
        tenant_id=user.tenant_id,
        episode_id=f2f.id,
        assessment_payload=_extract_f2f_reasoning_payload(f2f),
        request_id=str(f2f.id),
        log_label=f"f2f_id={f2f.id}",
    )

    log_event(
        db=db, tenant_id=str(user.tenant_id), user_id=user.user_id, role=user.role,
        action="FINALIZE_F2F", entity_type="f2f_encounter", entity_id=str(f2f.id),
        metadata={"performed_by_role": f2f.performed_by_role},
    )
    db.commit()
    db.refresh(f2f)

    return F2FFinalizeResponse(
        id=f2f.id,
        status=f2f.status,
        finalized_at=str(f2f.finalized_at) if f2f.finalized_at else None,
    )


F2FCreateRequest.model_rebuild()
F2FCreateResponse.model_rebuild()
F2FFinalizeRequest.model_rebuild()
F2FFinalizeResponse.model_rebuild()
