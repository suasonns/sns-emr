from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.patient_access import get_authorized_patient
from app.core.security import CurrentUser
from app.core.database import get_db
from app.core.permissions import require_roles
from app.models.benefit_period import BenefitPeriod
from app.models.f2f_encounter import F2FEncounter
from app.services.f2f_service import create_f2f, finalize_f2f


router = APIRouter(prefix="/f2f", tags=["F2F"])


# =========================================================
# REQUEST / RESPONSE SCHEMAS
# =========================================================

class F2FCreateRequest(BaseModel):
    patient_id: UUID
    benefit_period_id: UUID
    encounter_date: date

    performed_by_role: Literal[
        "MD",
        "NP",
    ]

    summary: Optional[str] = Field(default=None, max_length=5000)
    clinical_decline_summary: Optional[str] = Field(default=None, max_length=5000)

    # Functional scoring
    kps_score: Optional[int] = None
    pps_score_previous: Optional[int] = None
    pps_score_current: Optional[int] = None

    # Disease scoring
    fast_score: Optional[str] = None
    nyha_class: Optional[str] = None

    # ADL / decline
    adl_dependency_level: Optional[str] = None
    adl_dependency_count: Optional[int] = None
    is_bedbound: Optional[bool] = None

    # Objective decline indicators
    weight_loss_lbs: Optional[float] = None
    oral_intake_decline: Optional[bool] = None
    dysphagia: Optional[bool] = None
    hospitalizations_30d: Optional[int] = None
    oxygen_lpm_previous: Optional[float] = None
    oxygen_lpm_current: Optional[float] = None

    primary_diagnosis: Optional[str] = None
    secondary_conditions: Optional[str] = None


class F2FCreateResponse(BaseModel):
    id: UUID
    status: str
    encounter_date: date


class F2FFinalizeRequest(BaseModel):
    # Used when NP performed the F2F and physician review/attestation is captured on the encounter.
    attesting_provider_user_id: Optional[UUID] = None
    attesting_provider_role: Optional[
        Literal[
            "MD",
            "MEDICAL_DIRECTOR",
            "ALTERNATE_MEDICAL_DIRECTOR",
            "MEDICAL_DIRECTOR_DESIGNEE",
        ]
    ] = None
    attestation_summary: Optional[str] = Field(default=None, max_length=5000)


class F2FFinalizeResponse(BaseModel):
    id: UUID
    status: str
    finalized_at: Optional[str]


# =========================================================
# HELPERS
# =========================================================

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


def _validate_f2f_for_finalize(f2f: F2FEncounter) -> None:
    errors: list[str] = []

    # At least one scoring system required
    if not any([
        f2f.kps_score is not None,
        f2f.pps_score_current is not None,
        bool(f2f.fast_score),
        bool(f2f.nyha_class),
    ]):
        errors.append("At least one scoring system is required (KPS, PPS, FAST, or NYHA).")

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


# =========================================================
# CREATE F2F (DRAFT)
# =========================================================

@router.post("/", response_model=F2FCreateResponse)
def create_f2f_endpoint(
    request: F2FCreateRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(
        require_roles(["RN", "NP", "MD", "Administrator", "DPCS"])
    ),
):
    get_authorized_patient(db, request.patient_id, user)

    # Validate benefit period ownership + encounter date
    bp = (
        db.query(BenefitPeriod)
        .filter(
            BenefitPeriod.id == request.benefit_period_id,
            BenefitPeriod.patient_id == request.patient_id,
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

    # Create draft through service
    f2f = create_f2f(
        db=db,
        patient_id=request.patient_id,
        benefit_period_id=request.benefit_period_id,
        encounter_date=request.encounter_date,
        performed_by_role=request.performed_by_role,
        performed_by_user_id=user.user_id,
        summary=request.summary,
    )

    # Persist structured data
    f2f.kps_score = request.kps_score
    f2f.pps_score_previous = request.pps_score_previous
    f2f.pps_score_current = request.pps_score_current
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
    user: CurrentUser = Depends(
        require_roles(["NP", "MD", "Administrator", "DPCS"])
    ),
):
    f2f = db.query(F2FEncounter).filter(F2FEncounter.id == f2f_id).first()

    if not f2f:
        raise HTTPException(status_code=404, detail="F2F encounter not found.")

    get_authorized_patient(db, f2f.patient_id, user)

    if not f2f.summary:
        f2f.summary = _generate_f2f_summary(f2f)

    # ADR / CMS-oriented validation
    _validate_f2f_for_finalize(f2f)

    # NP performed F2F → capture physician review/attestation on the encounter
    if f2f.performed_by_role == "NP":
        if user.role not in {"MD", "Administrator", "DPCS"}:
            raise HTTPException(
                status_code=403,
                detail="Physician review is required to finalize NP-performed F2F.",
            )

        if not request.attestation_summary:
            raise HTTPException(
                status_code=422,
                detail="Attestation summary is required for NP-performed F2F.",
            )

        f2f.attesting_provider_user_id = request.attesting_provider_user_id or user.user_id
        f2f.attested_at = datetime.now(timezone.utc)

    # Finalize through service
    f2f = finalize_f2f(db=db, f2f=f2f)

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