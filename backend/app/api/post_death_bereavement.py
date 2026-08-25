# api/post_death_bereavement.py

"""
Post-Death Bereavement Assessment API -- third of five planned Bereavement
sub-sections (see chart-section-bereavement-post-death,
models/post_death_bereavement_assessment.py).
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
from app.models.bereavement_poc import BereavementPOC
from app.models.post_death_bereavement_assessment import PostDeathBereavementAssessment
from app.services.audit_events import audit_event
from app.services.bereavement_poc_catalog import (
    BEREAVEMENT_POC_GOALS,
    BEREAVEMENT_POC_INTERVENTIONS,
    default_goals_for_risk,
    default_interventions_for_risk,
)
from app.services.bereavement_risk_scoring import BEREAVEMENT_RISK_ITEMS, score_bereavement_risk

router = APIRouter(prefix="/post-death-bereavement", tags=["bereavement"])

BEREAVEMENT_VIEW_ROLES = ["LVN", "RN", "NP", "PA", "MD", "MSW", "SC", "Chaplain", "CHHA", "Surveyor"]
BEREAVEMENT_EDIT_ROLES = ["MSW", "SC", "Chaplain", "RN", "NP", "PA", "MD"]

_PRIMARY_BEREAVED_FIELDS = [
    "no_family",
    "primary_first_name",
    "primary_last_name",
    "primary_relationship_to_patient",
    "primary_address",
    "primary_city",
    "primary_state",
    "primary_zip",
    "primary_home_phone",
    "primary_cell_phone",
    "primary_email",
    "primary_was_caregiver",
]


class RiskItemEntry(BaseModel):
    checked: bool = False
    note: str | None = None


class GoalEntry(BaseModel):
    key: str
    label: str
    selected: bool = True
    target_date: date | None = None
    notes: str | None = None


class InterventionEntry(BaseModel):
    key: str
    label: str
    selected: bool = True
    notes: str | None = None


class PostDeathBereavementCreate(BaseModel):
    patient_id: uuid.UUID
    bereavement_assessment_id: uuid.UUID | None = None
    bereavement_poc_id: uuid.UUID | None = None
    staff_assigned: uuid.UUID | None = None
    discipline: str | None = None
    visit_type: str | None = None
    visit_mode: str | None = None
    visit_date: date | None = None
    time_in: str | None = None
    time_out: str | None = None
    duration_minutes: int | None = None

    # Primary bereaved -- inherited from the linked assessment/POC (in that
    # order of preference) when omitted.
    no_family: bool | None = None
    primary_first_name: str | None = None
    primary_last_name: str | None = None
    primary_relationship_to_patient: str | None = None
    primary_address: str | None = None
    primary_city: str | None = None
    primary_state: str | None = None
    primary_zip: str | None = None
    primary_home_phone: str | None = None
    primary_cell_phone: str | None = None
    primary_email: str | None = None
    primary_was_caregiver: bool | None = None

    date_of_death: date | None = None
    place_of_death: str | None = None
    death_expected: bool | None = None
    pcg_present_at_death: bool | None = None
    family_present_at_death: bool | None = None
    funeral_plans_finalized: bool | None = None
    funeral_home_name: str | None = None

    condolence_call_date: date | None = None
    condolence_call_by: uuid.UUID | None = None
    condolence_call_notes: str | None = None

    emotional_status_narrative: str | None = None

    survivor_support_system_adequate: bool | None = None
    desires_intensive_bereavement_support: bool | None = None
    complicated_grief_reactions_observed: bool | None = None
    additional_risk_factors_since_initial: bool | None = None
    additional_risk_notes: str | None = None

    risk_items: dict[str, RiskItemEntry] = Field(default_factory=dict)
    risk_other_note: str | None = None

    # If omitted, goals/interventions are auto-populated from the reassessed
    # risk-level catalog (see bereavement_poc_catalog).
    goals: list[GoalEntry] | None = None
    interventions: list[InterventionEntry] | None = None
    other_interventions: str | None = None
    plan_of_care_narrative: str | None = None

    narrative: str | None = None


class PostDeathBereavementUpdate(BaseModel):
    bereavement_assessment_id: uuid.UUID | None = None
    bereavement_poc_id: uuid.UUID | None = None
    staff_assigned: uuid.UUID | None = None
    discipline: str | None = None
    visit_type: str | None = None
    visit_mode: str | None = None
    visit_date: date | None = None
    time_in: str | None = None
    time_out: str | None = None
    duration_minutes: int | None = None

    no_family: bool | None = None
    primary_first_name: str | None = None
    primary_last_name: str | None = None
    primary_relationship_to_patient: str | None = None
    primary_address: str | None = None
    primary_city: str | None = None
    primary_state: str | None = None
    primary_zip: str | None = None
    primary_home_phone: str | None = None
    primary_cell_phone: str | None = None
    primary_email: str | None = None
    primary_was_caregiver: bool | None = None

    date_of_death: date | None = None
    place_of_death: str | None = None
    death_expected: bool | None = None
    pcg_present_at_death: bool | None = None
    family_present_at_death: bool | None = None
    funeral_plans_finalized: bool | None = None
    funeral_home_name: str | None = None

    condolence_call_date: date | None = None
    condolence_call_by: uuid.UUID | None = None
    condolence_call_notes: str | None = None

    emotional_status_narrative: str | None = None

    survivor_support_system_adequate: bool | None = None
    desires_intensive_bereavement_support: bool | None = None
    complicated_grief_reactions_observed: bool | None = None
    additional_risk_factors_since_initial: bool | None = None
    additional_risk_notes: str | None = None

    risk_items: dict[str, RiskItemEntry] | None = None
    risk_other_note: str | None = None

    goals: list[GoalEntry] | None = None
    interventions: list[InterventionEntry] | None = None
    other_interventions: str | None = None
    plan_of_care_narrative: str | None = None

    narrative: str | None = None


class PostDeathBereavementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    patient_id: uuid.UUID
    bereavement_assessment_id: uuid.UUID | None = None
    bereavement_poc_id: uuid.UUID | None = None
    status: str

    entered_by: uuid.UUID
    staff_assigned: uuid.UUID | None = None
    discipline: str | None = None
    visit_type: str | None = None
    visit_mode: str | None = None
    visit_date: date | None = None
    time_in: str | None = None
    time_out: str | None = None
    duration_minutes: int | None = None

    no_family: bool
    primary_first_name: str | None = None
    primary_last_name: str | None = None
    primary_relationship_to_patient: str | None = None
    primary_address: str | None = None
    primary_city: str | None = None
    primary_state: str | None = None
    primary_zip: str | None = None
    primary_home_phone: str | None = None
    primary_cell_phone: str | None = None
    primary_email: str | None = None
    primary_was_caregiver: bool | None = None

    date_of_death: date | None = None
    place_of_death: str | None = None
    death_expected: bool | None = None
    pcg_present_at_death: bool | None = None
    family_present_at_death: bool | None = None
    funeral_plans_finalized: bool | None = None
    funeral_home_name: str | None = None

    condolence_call_date: date | None = None
    condolence_call_by: uuid.UUID | None = None
    condolence_call_notes: str | None = None

    emotional_status_narrative: str | None = None

    survivor_support_system_adequate: bool | None = None
    desires_intensive_bereavement_support: bool | None = None
    complicated_grief_reactions_observed: bool | None = None
    additional_risk_factors_since_initial: bool | None = None
    additional_risk_notes: str | None = None

    risk_items: dict
    risk_other_note: str | None = None
    risk_total_score: int
    risk_level: str | None = None

    goals: list
    interventions: list
    other_interventions: str | None = None
    plan_of_care_narrative: str | None = None

    narrative: str | None = None

    signed_by: uuid.UUID | None = None
    signed_at: datetime | None = None

    created_at: datetime
    updated_at: datetime | None = None


def _resolve_linked(
    db: Session, user: CurrentUser, patient_id: uuid.UUID, assessment_id, poc_id
) -> tuple[BereavementAssessment | None, BereavementPOC | None]:
    linked_assessment = None
    if assessment_id is not None:
        linked_assessment = (
            db.query(BereavementAssessment)
            .filter(
                BereavementAssessment.id == assessment_id,
                BereavementAssessment.tenant_id == user.tenant_id,
                BereavementAssessment.patient_id == patient_id,
            )
            .one_or_none()
        )
        if linked_assessment is None:
            raise HTTPException(status_code=404, detail="Linked bereavement assessment not found")

    linked_poc = None
    if poc_id is not None:
        linked_poc = (
            db.query(BereavementPOC)
            .filter(
                BereavementPOC.id == poc_id,
                BereavementPOC.tenant_id == user.tenant_id,
                BereavementPOC.patient_id == patient_id,
            )
            .one_or_none()
        )
        if linked_poc is None:
            raise HTTPException(status_code=404, detail="Linked bereavement POC not found")

    return linked_assessment, linked_poc


def _get_owned(db: Session, record_id: uuid.UUID, user: CurrentUser) -> PostDeathBereavementAssessment:
    record = (
        db.query(PostDeathBereavementAssessment)
        .filter(
            PostDeathBereavementAssessment.id == record_id,
            PostDeathBereavementAssessment.tenant_id == user.tenant_id,
        )
        .one_or_none()
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Post-death bereavement assessment not found")
    return record


@router.get("/risk-items")
def get_risk_item_catalog(user: CurrentUser = Depends(require_roles(BEREAVEMENT_VIEW_ROLES))):
    return BEREAVEMENT_RISK_ITEMS


@router.get("/catalog")
def get_plan_catalog(user: CurrentUser = Depends(require_roles(BEREAVEMENT_VIEW_ROLES))):
    return {"goals": BEREAVEMENT_POC_GOALS, "interventions": BEREAVEMENT_POC_INTERVENTIONS}


@router.get("/defaults")
def get_plan_defaults(
    risk_level: str = "LOW",
    user: CurrentUser = Depends(require_roles(BEREAVEMENT_VIEW_ROLES)),
):
    return {
        "goals": default_goals_for_risk(risk_level),
        "interventions": default_interventions_for_risk(risk_level),
    }


@router.post("", response_model=PostDeathBereavementRead, status_code=status.HTTP_201_CREATED)
def create_post_death_bereavement(
    payload: PostDeathBereavementCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(BEREAVEMENT_EDIT_ROLES)),
):
    patient = get_authorized_patient(db, payload.patient_id, user)

    linked_assessment, linked_poc = _resolve_linked(
        db, user, patient.id, payload.bereavement_assessment_id, payload.bereavement_poc_id
    )

    def _inherited(field: str):
        explicit = getattr(payload, field)
        if explicit is not None:
            return explicit
        if linked_assessment is not None and getattr(linked_assessment, field, None) is not None:
            return getattr(linked_assessment, field)
        if linked_poc is not None:
            return getattr(linked_poc, field, None)
        return None

    risk_items_dict = {k: v.model_dump() for k, v in payload.risk_items.items()}
    total, level = score_bereavement_risk(risk_items_dict)

    goals = (
        [g.model_dump() for g in payload.goals]
        if payload.goals is not None
        else default_goals_for_risk(level)
    )
    interventions = (
        [i.model_dump() for i in payload.interventions]
        if payload.interventions is not None
        else default_interventions_for_risk(level)
    )

    record = PostDeathBereavementAssessment(
        tenant_id=patient.tenant_id,
        patient_id=patient.id,
        bereavement_assessment_id=payload.bereavement_assessment_id,
        bereavement_poc_id=payload.bereavement_poc_id,
        entered_by=user.user_id,
        created_by=user.user_id,
        staff_assigned=payload.staff_assigned,
        discipline=payload.discipline,
        visit_type=payload.visit_type,
        visit_mode=payload.visit_mode,
        visit_date=payload.visit_date,
        time_in=payload.time_in,
        time_out=payload.time_out,
        duration_minutes=payload.duration_minutes,
        no_family=_inherited("no_family") or False,
        primary_first_name=_inherited("primary_first_name"),
        primary_last_name=_inherited("primary_last_name"),
        primary_relationship_to_patient=_inherited("primary_relationship_to_patient"),
        primary_address=_inherited("primary_address"),
        primary_city=_inherited("primary_city"),
        primary_state=_inherited("primary_state"),
        primary_zip=_inherited("primary_zip"),
        primary_home_phone=_inherited("primary_home_phone"),
        primary_cell_phone=_inherited("primary_cell_phone"),
        primary_email=_inherited("primary_email"),
        primary_was_caregiver=_inherited("primary_was_caregiver"),
        date_of_death=payload.date_of_death or (linked_poc.date_of_death if linked_poc else None),
        place_of_death=payload.place_of_death,
        death_expected=payload.death_expected,
        pcg_present_at_death=payload.pcg_present_at_death,
        family_present_at_death=payload.family_present_at_death,
        funeral_plans_finalized=payload.funeral_plans_finalized,
        funeral_home_name=payload.funeral_home_name,
        condolence_call_date=payload.condolence_call_date,
        condolence_call_by=payload.condolence_call_by,
        condolence_call_notes=payload.condolence_call_notes,
        emotional_status_narrative=payload.emotional_status_narrative,
        survivor_support_system_adequate=payload.survivor_support_system_adequate,
        desires_intensive_bereavement_support=payload.desires_intensive_bereavement_support,
        complicated_grief_reactions_observed=payload.complicated_grief_reactions_observed,
        additional_risk_factors_since_initial=payload.additional_risk_factors_since_initial,
        additional_risk_notes=payload.additional_risk_notes,
        risk_items=risk_items_dict,
        risk_other_note=payload.risk_other_note,
        risk_total_score=total,
        risk_level=level,
        goals=goals,
        interventions=interventions,
        other_interventions=payload.other_interventions,
        plan_of_care_narrative=payload.plan_of_care_narrative,
        narrative=payload.narrative,
    )

    db.add(record)
    db.flush()

    audit_event(
        db=db,
        tenant_id=str(user.tenant_id),
        user_id=str(user.user_id),
        role=(user.role or "").strip().upper(),
        action="POST_DEATH_BEREAVEMENT_CREATED",
        entity_type="POST_DEATH_BEREAVEMENT_ASSESSMENT",
        entity_id=str(record.id),
        meta={"patient_id": str(record.patient_id), "risk_level": record.risk_level},
    )

    db.commit()
    db.refresh(record)
    return record


@router.get("/patient/{patient_id}", response_model=list[PostDeathBereavementRead])
def list_post_death_bereavement(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(BEREAVEMENT_VIEW_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)
    return (
        db.query(PostDeathBereavementAssessment)
        .filter(
            PostDeathBereavementAssessment.tenant_id == patient.tenant_id,
            PostDeathBereavementAssessment.patient_id == patient.id,
        )
        .order_by(PostDeathBereavementAssessment.created_at.desc())
        .all()
    )


@router.get("/{record_id}", response_model=PostDeathBereavementRead)
def get_post_death_bereavement(
    record_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(BEREAVEMENT_VIEW_ROLES)),
):
    record = _get_owned(db, record_id, user)
    get_authorized_patient(db, record.patient_id, user)
    return record


@router.patch("/{record_id}", response_model=PostDeathBereavementRead)
def update_post_death_bereavement(
    record_id: uuid.UUID,
    payload: PostDeathBereavementUpdate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(BEREAVEMENT_EDIT_ROLES)),
):
    record = _get_owned(db, record_id, user)
    get_authorized_patient(db, record.patient_id, user)

    if record.status == "SIGNED":
        raise HTTPException(status_code=409, detail="Assessment is signed and locked; unlock is not yet supported")

    changes = payload.model_dump(exclude_unset=True)

    if "bereavement_assessment_id" in changes or "bereavement_poc_id" in changes:
        _resolve_linked(
            db,
            user,
            record.patient_id,
            changes.get("bereavement_assessment_id", record.bereavement_assessment_id),
            changes.get("bereavement_poc_id", record.bereavement_poc_id),
        )

    risk_items_payload = changes.pop("risk_items", None)
    goals_payload = changes.pop("goals", None)
    interventions_payload = changes.pop("interventions", None)

    for field_name, value in changes.items():
        setattr(record, field_name, value)

    if risk_items_payload is not None:
        record.risk_items = risk_items_payload
        total, level = score_bereavement_risk(record.risk_items or {})
        record.risk_total_score = total
        record.risk_level = level

    if goals_payload is not None:
        record.goals = goals_payload
    if interventions_payload is not None:
        record.interventions = interventions_payload

    record.updated_by = user.user_id
    record.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(record)
    return record


@router.post("/{record_id}/sign", response_model=PostDeathBereavementRead)
def sign_post_death_bereavement(
    record_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(BEREAVEMENT_EDIT_ROLES)),
):
    record = _get_owned(db, record_id, user)
    get_authorized_patient(db, record.patient_id, user)

    if record.status == "SIGNED":
        raise HTTPException(status_code=409, detail="Assessment is already signed")

    record.status = "SIGNED"
    record.signed_by = user.user_id
    record.signed_at = datetime.now(timezone.utc)
    record.updated_by = user.user_id
    record.updated_at = datetime.now(timezone.utc)

    audit_event(
        db=db,
        tenant_id=str(user.tenant_id),
        user_id=str(user.user_id),
        role=(user.role or "").strip().upper(),
        action="POST_DEATH_BEREAVEMENT_SIGNED",
        entity_type="POST_DEATH_BEREAVEMENT_ASSESSMENT",
        entity_id=str(record.id),
        meta={"patient_id": str(record.patient_id), "risk_level": record.risk_level},
    )

    db.commit()
    db.refresh(record)
    return record
