# api/bereavement.py

"""
Comprehensive Bereavement Assessment (Initial Assessment) API.

First of five planned Bereavement sub-sections. Bereavement POC,
Post-Death Assessment, Bereavement Letters, and Post-Death Support are
tracked as follow-on work (see chart-section-bereavement-poc,
chart-section-bereavement-post-death, chart-section-bereavement-letters,
chart-section-bereavement-support).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.patient_access import get_authorized_patient
from app.core.permissions import require_roles
from app.core.security import CurrentUser
from app.models.bereavement_assessment import BereavementAssessment
from app.services.audit_events import audit_event
from app.services.bereavement_risk_scoring import BEREAVEMENT_RISK_ITEMS, score_bereavement_risk

router = APIRouter(prefix="/bereavement-assessments", tags=["bereavement"])

BEREAVEMENT_VIEW_ROLES = ["LVN", "RN", "NP", "PA", "MD", "MSW", "SC", "Chaplain", "CHHA", "Surveyor"]
BEREAVEMENT_EDIT_ROLES = ["MSW", "SC", "Chaplain", "RN", "NP", "PA", "MD"]


class AdditionalBereavedEntry(BaseModel):
    name: str = Field(min_length=1)
    relationship_to_patient: str | None = None
    address: str | None = None
    phone: str | None = None
    specific_concerns: str | None = None


class RiskItemEntry(BaseModel):
    checked: bool = False
    note: str | None = None


class BereavementAssessmentCreate(BaseModel):
    patient_id: uuid.UUID
    staff_assigned: uuid.UUID | None = None
    discipline: str | None = None
    care_level: str | None = None
    visit_type: str | None = None
    visit_mode: str | None = None
    visit_date: date | None = None
    time_in: str | None = None
    time_out: str | None = None
    duration_minutes: int | None = None

    no_family: bool = False
    primary_first_name: str | None = None
    primary_last_name: str | None = None
    primary_age: int | None = None
    primary_gender: str | None = None
    primary_address: str | None = None
    primary_city: str | None = None
    primary_state: str | None = None
    primary_zip: str | None = None
    primary_home_phone: str | None = None
    primary_work_phone: str | None = None
    primary_cell_phone: str | None = None
    primary_email: str | None = None
    primary_relationship_to_patient: str | None = None
    primary_was_caregiver: bool | None = None

    risk_items: dict[str, RiskItemEntry] = Field(default_factory=dict)
    risk_other_note: str | None = None

    additional_bereaved: list[AdditionalBereavedEntry] = Field(default_factory=list)
    narrative: str | None = None


class BereavementAssessmentUpdate(BereavementAssessmentCreate):
    patient_id: uuid.UUID | None = None  # not changeable, ignored on update


class BereavementAssessmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    patient_id: uuid.UUID
    status: str

    entered_by: uuid.UUID
    staff_assigned: uuid.UUID | None = None
    discipline: str | None = None
    care_level: str | None = None
    visit_type: str | None = None
    visit_mode: str | None = None
    visit_date: date | None = None
    time_in: str | None = None
    time_out: str | None = None
    duration_minutes: int | None = None

    no_family: bool
    primary_first_name: str | None = None
    primary_last_name: str | None = None
    primary_age: int | None = None
    primary_gender: str | None = None
    primary_address: str | None = None
    primary_city: str | None = None
    primary_state: str | None = None
    primary_zip: str | None = None
    primary_home_phone: str | None = None
    primary_work_phone: str | None = None
    primary_cell_phone: str | None = None
    primary_email: str | None = None
    primary_relationship_to_patient: str | None = None
    primary_was_caregiver: bool | None = None

    risk_items: dict
    risk_other_note: str | None = None
    risk_total_score: int
    risk_level: str | None = None

    additional_bereaved: list

    narrative: str | None = None

    signed_by: uuid.UUID | None = None
    signed_at: datetime | None = None

    created_at: datetime
    updated_at: datetime | None = None


def _apply_fields(assessment: BereavementAssessment, payload: BaseModel) -> None:
    changes = payload.model_dump(exclude_unset=True, exclude={"patient_id"})
    risk_items_payload = changes.pop("risk_items", None)
    additional_bereaved_payload = changes.pop("additional_bereaved", None)

    for field_name, value in changes.items():
        setattr(assessment, field_name, value)

    if risk_items_payload is not None:
        assessment.risk_items = risk_items_payload
    if additional_bereaved_payload is not None:
        assessment.additional_bereaved = additional_bereaved_payload

    total, level = score_bereavement_risk(assessment.risk_items or {})
    assessment.risk_total_score = total
    assessment.risk_level = level


def _get_owned_assessment(db: Session, assessment_id: uuid.UUID, user: CurrentUser) -> BereavementAssessment:
    assessment = (
        db.query(BereavementAssessment)
        .filter(BereavementAssessment.id == assessment_id, BereavementAssessment.tenant_id == user.tenant_id)
        .one_or_none()
    )
    if assessment is None:
        raise HTTPException(status_code=404, detail="Bereavement assessment not found")
    return assessment


@router.get("/risk-items")
def get_risk_item_catalog(user: CurrentUser = Depends(require_roles(BEREAVEMENT_VIEW_ROLES))):
    return BEREAVEMENT_RISK_ITEMS


@router.post("", response_model=BereavementAssessmentRead, status_code=status.HTTP_201_CREATED)
def create_bereavement_assessment(
    payload: BereavementAssessmentCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(BEREAVEMENT_EDIT_ROLES)),
):
    patient = get_authorized_patient(db, payload.patient_id, user)

    assessment = BereavementAssessment(
        tenant_id=patient.tenant_id,
        patient_id=patient.id,
        entered_by=user.user_id,
        created_by=user.user_id,
    )
    _apply_fields(assessment, payload)

    db.add(assessment)
    db.flush()

    audit_event(
        db=db,
        tenant_id=str(user.tenant_id),
        user_id=str(user.user_id),
        role=(user.role or "").strip().upper(),
        action="BEREAVEMENT_ASSESSMENT_CREATED",
        entity_type="BEREAVEMENT_ASSESSMENT",
        entity_id=str(assessment.id),
        meta={"patient_id": str(assessment.patient_id), "risk_level": assessment.risk_level},
    )

    db.commit()
    db.refresh(assessment)
    return assessment


@router.get("/patient/{patient_id}", response_model=list[BereavementAssessmentRead])
def list_bereavement_assessments(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(BEREAVEMENT_VIEW_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)
    return (
        db.query(BereavementAssessment)
        .filter(
            BereavementAssessment.tenant_id == patient.tenant_id,
            BereavementAssessment.patient_id == patient.id,
        )
        .order_by(BereavementAssessment.created_at.desc())
        .all()
    )


@router.get("/{assessment_id}", response_model=BereavementAssessmentRead)
def get_bereavement_assessment(
    assessment_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(BEREAVEMENT_VIEW_ROLES)),
):
    assessment = _get_owned_assessment(db, assessment_id, user)
    get_authorized_patient(db, assessment.patient_id, user)
    return assessment


@router.patch("/{assessment_id}", response_model=BereavementAssessmentRead)
def update_bereavement_assessment(
    assessment_id: uuid.UUID,
    payload: BereavementAssessmentUpdate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(BEREAVEMENT_EDIT_ROLES)),
):
    assessment = _get_owned_assessment(db, assessment_id, user)
    get_authorized_patient(db, assessment.patient_id, user)

    if assessment.status == "SIGNED":
        raise HTTPException(status_code=409, detail="Assessment is signed and locked; unlock is not yet supported")

    _apply_fields(assessment, payload)
    assessment.updated_by = user.user_id
    assessment.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(assessment)
    return assessment


@router.post("/{assessment_id}/sign", response_model=BereavementAssessmentRead)
def sign_bereavement_assessment(
    assessment_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(BEREAVEMENT_EDIT_ROLES)),
):
    assessment = _get_owned_assessment(db, assessment_id, user)
    get_authorized_patient(db, assessment.patient_id, user)

    if assessment.status == "SIGNED":
        raise HTTPException(status_code=409, detail="Assessment is already signed")
    if not assessment.primary_first_name and not assessment.no_family:
        raise HTTPException(status_code=400, detail="Primary bereaved information is required before signing")

    assessment.status = "SIGNED"
    assessment.signed_by = user.user_id
    assessment.signed_at = datetime.now(timezone.utc)
    assessment.updated_by = user.user_id
    assessment.updated_at = datetime.now(timezone.utc)

    audit_event(
        db=db,
        tenant_id=str(user.tenant_id),
        user_id=str(user.user_id),
        role=(user.role or "").strip().upper(),
        action="BEREAVEMENT_ASSESSMENT_SIGNED",
        entity_type="BEREAVEMENT_ASSESSMENT",
        entity_id=str(assessment.id),
        meta={"patient_id": str(assessment.patient_id), "risk_level": assessment.risk_level},
    )

    db.commit()
    db.refresh(assessment)
    return assessment
