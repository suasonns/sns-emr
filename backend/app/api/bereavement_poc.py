# api/bereavement_poc.py

"""
Bereavement Plan of Care (POC) API -- second of five planned Bereavement
sub-sections (see chart-section-bereavement-poc, models/bereavement_poc.py,
services/bereavement_poc_catalog.py).
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
from app.services.audit_events import audit_event
from app.services.bereavement_poc_catalog import (
    BEREAVEMENT_POC_GOALS,
    BEREAVEMENT_POC_INTERVENTIONS,
    default_action_plan,
    default_goals_for_risk,
    default_interventions_for_risk,
)

router = APIRouter(prefix="/bereavement-poc", tags=["bereavement"])

BEREAVEMENT_VIEW_ROLES = ["LVN", "RN", "NP", "PA", "MD", "MSW", "SC", "Chaplain", "CHHA", "Surveyor"]
BEREAVEMENT_EDIT_ROLES = ["MSW", "SC", "Chaplain", "RN", "NP", "PA", "MD"]


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


class ActionPlanEntry(BaseModel):
    month_offset_days: int | None = None
    label: str
    contact_type: str | None = "PHONE"
    required: bool = True
    included: bool = True
    planned_date: date | None = None
    completed_date: date | None = None
    completed_by: uuid.UUID | None = None
    notes: str | None = None


class BereavementPOCCreate(BaseModel):
    patient_id: uuid.UUID
    bereavement_assessment_id: uuid.UUID | None = None
    staff_assigned: uuid.UUID | None = None
    discipline: str | None = None
    date_of_death: date | None = None
    risk_level: str | None = None

    # Primary bereaved -- if bereavement_assessment_id is supplied and these
    # are omitted, they are copied from the linked assessment automatically.
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

    # If omitted, goals/interventions/action_plan are auto-populated from the
    # risk-level catalog + date_of_death (see bereavement_poc_catalog).
    goals: list[GoalEntry] | None = None
    interventions: list[InterventionEntry] | None = None
    other_interventions: str | None = None
    action_plan: list[ActionPlanEntry] | None = None

    narrative: str | None = None


class BereavementPOCUpdate(BaseModel):
    bereavement_assessment_id: uuid.UUID | None = None
    staff_assigned: uuid.UUID | None = None
    discipline: str | None = None
    date_of_death: date | None = None
    risk_level: str | None = None

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

    goals: list[GoalEntry] | None = None
    interventions: list[InterventionEntry] | None = None
    other_interventions: str | None = None
    action_plan: list[ActionPlanEntry] | None = None
    narrative: str | None = None
    closed_early: bool | None = None
    closed_reason: str | None = None


class BereavementPOCRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    patient_id: uuid.UUID
    bereavement_assessment_id: uuid.UUID | None = None
    status: str

    entered_by: uuid.UUID
    staff_assigned: uuid.UUID | None = None
    discipline: str | None = None

    date_of_death: date | None = None
    risk_level: str | None = None
    risk_source: str | None = None  # SCORED | MANUAL
    risk_score: int | None = None

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

    goals: list
    interventions: list
    other_interventions: str | None = None
    action_plan: list

    narrative: str | None = None

    closed_early: bool
    closed_reason: str | None = None

    signed_by: uuid.UUID | None = None
    signed_at: datetime | None = None

    created_at: datetime
    updated_at: datetime | None = None


def _get_owned_poc(db: Session, poc_id: uuid.UUID, user: CurrentUser) -> BereavementPOC:
    poc = (
        db.query(BereavementPOC)
        .filter(BereavementPOC.id == poc_id, BereavementPOC.tenant_id == user.tenant_id)
        .one_or_none()
    )
    if poc is None:
        raise HTTPException(status_code=404, detail="Bereavement POC not found")
    return poc


@router.get("/catalog")
def get_poc_catalog(user: CurrentUser = Depends(require_roles(BEREAVEMENT_VIEW_ROLES))):
    return {"goals": BEREAVEMENT_POC_GOALS, "interventions": BEREAVEMENT_POC_INTERVENTIONS}


@router.get("/defaults")
def get_poc_defaults(
    risk_level: str = "LOW",
    date_of_death: date | None = None,
    user: CurrentUser = Depends(require_roles(BEREAVEMENT_VIEW_ROLES)),
):
    """
    Computes the standard goals/interventions/13-month action plan for a given
    risk level (+ optional date of death for concrete planned dates). Used by
    the frontend to (re)populate a POC when the risk level or date of death
    changes, without duplicating the catalog/schedule logic in JS.
    """
    return {
        "goals": default_goals_for_risk(risk_level),
        "interventions": default_interventions_for_risk(risk_level),
        "action_plan": default_action_plan(risk_level, date_of_death),
    }


@router.post("", response_model=BereavementPOCRead, status_code=status.HTTP_201_CREATED)
def create_bereavement_poc(
    payload: BereavementPOCCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(BEREAVEMENT_EDIT_ROLES)),
):
    patient = get_authorized_patient(db, payload.patient_id, user)

    linked_assessment = None
    if payload.bereavement_assessment_id is not None:
        linked_assessment = (
            db.query(BereavementAssessment)
            .filter(
                BereavementAssessment.id == payload.bereavement_assessment_id,
                BereavementAssessment.tenant_id == user.tenant_id,
                BereavementAssessment.patient_id == patient.id,
            )
            .one_or_none()
        )
        if linked_assessment is None:
            raise HTTPException(status_code=404, detail="Linked bereavement assessment not found")

    risk_level = payload.risk_level or (linked_assessment.risk_level if linked_assessment else None) or "LOW"

    # Risk provenance: SCORED when inherited from a linked, weighted-score
    # assessment and the caller didn't override it with a different value;
    # MANUAL otherwise (clinician picked it directly with no scored backing).
    if linked_assessment is not None and not payload.risk_level:
        risk_source = "SCORED"
        risk_score = linked_assessment.risk_total_score
    elif linked_assessment is not None and payload.risk_level == linked_assessment.risk_level:
        risk_source = "SCORED"
        risk_score = linked_assessment.risk_total_score
    else:
        risk_source = "MANUAL"
        risk_score = None

    def _inherited(field: str):
        explicit = getattr(payload, field)
        if explicit is not None:
            return explicit
        return getattr(linked_assessment, field) if linked_assessment is not None else None

    goals = (
        [g.model_dump() for g in payload.goals]
        if payload.goals is not None
        else default_goals_for_risk(risk_level)
    )
    interventions = (
        [i.model_dump() for i in payload.interventions]
        if payload.interventions is not None
        else default_interventions_for_risk(risk_level)
    )
    action_plan = (
        [a.model_dump(mode="json") for a in payload.action_plan]
        if payload.action_plan is not None
        else default_action_plan(risk_level, payload.date_of_death)
    )

    poc = BereavementPOC(
        tenant_id=patient.tenant_id,
        patient_id=patient.id,
        bereavement_assessment_id=payload.bereavement_assessment_id,
        entered_by=user.user_id,
        created_by=user.user_id,
        staff_assigned=payload.staff_assigned,
        discipline=payload.discipline,
        date_of_death=payload.date_of_death,
        risk_level=risk_level,
        risk_source=risk_source,
        risk_score=risk_score,
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
        goals=goals,
        interventions=interventions,
        other_interventions=payload.other_interventions,
        action_plan=action_plan,
        narrative=payload.narrative,
    )

    db.add(poc)
    db.flush()

    audit_event(
        db=db,
        tenant_id=str(user.tenant_id),
        user_id=str(user.user_id),
        role=(user.role or "").strip().upper(),
        action="BEREAVEMENT_POC_CREATED",
        entity_type="BEREAVEMENT_POC",
        entity_id=str(poc.id),
        meta={"patient_id": str(poc.patient_id), "risk_level": poc.risk_level},
    )

    db.commit()
    db.refresh(poc)
    return poc


@router.get("/patient/{patient_id}", response_model=list[BereavementPOCRead])
def list_bereavement_pocs(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(BEREAVEMENT_VIEW_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)
    return (
        db.query(BereavementPOC)
        .filter(BereavementPOC.tenant_id == patient.tenant_id, BereavementPOC.patient_id == patient.id)
        .order_by(BereavementPOC.created_at.desc())
        .all()
    )


@router.get("/{poc_id}", response_model=BereavementPOCRead)
def get_bereavement_poc(
    poc_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(BEREAVEMENT_VIEW_ROLES)),
):
    poc = _get_owned_poc(db, poc_id, user)
    get_authorized_patient(db, poc.patient_id, user)
    return poc


@router.patch("/{poc_id}", response_model=BereavementPOCRead)
def update_bereavement_poc(
    poc_id: uuid.UUID,
    payload: BereavementPOCUpdate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(BEREAVEMENT_EDIT_ROLES)),
):
    poc = _get_owned_poc(db, poc_id, user)
    get_authorized_patient(db, poc.patient_id, user)

    if poc.status == "SIGNED":
        raise HTTPException(status_code=409, detail="POC is signed and locked; unlock is not yet supported")

    changes = payload.model_dump(exclude_unset=True)
    goals_payload = changes.pop("goals", None)
    interventions_payload = changes.pop("interventions", None)
    action_plan_payload = changes.pop("action_plan", None)
    risk_level_explicit = "risk_level" in changes
    assessment_id_changed = "bereavement_assessment_id" in changes

    for field_name, value in changes.items():
        setattr(poc, field_name, value)

    # Re-derive risk provenance whenever risk_level or the linked assessment
    # changes, so risk_source/risk_score never go stale.
    if risk_level_explicit or assessment_id_changed:
        linked_assessment = None
        if poc.bereavement_assessment_id is not None:
            linked_assessment = (
                db.query(BereavementAssessment)
                .filter(
                    BereavementAssessment.id == poc.bereavement_assessment_id,
                    BereavementAssessment.tenant_id == user.tenant_id,
                    BereavementAssessment.patient_id == poc.patient_id,
                )
                .one_or_none()
            )
            if linked_assessment is None:
                raise HTTPException(status_code=404, detail="Linked bereavement assessment not found")

        if assessment_id_changed and not risk_level_explicit and linked_assessment is not None:
            # Newly linked (or re-linked) assessment and caller didn't also
            # override risk_level -- adopt the assessment's scored value.
            poc.risk_level = linked_assessment.risk_level

        if linked_assessment is not None and poc.risk_level == linked_assessment.risk_level:
            poc.risk_source = "SCORED"
            poc.risk_score = linked_assessment.risk_total_score
        else:
            poc.risk_source = "MANUAL"
            poc.risk_score = None

    if goals_payload is not None:
        poc.goals = goals_payload
    if interventions_payload is not None:
        poc.interventions = interventions_payload
    if action_plan_payload is not None:
        poc.action_plan = [
            {**entry, "planned_date": _iso(entry.get("planned_date")), "completed_date": _iso(entry.get("completed_date")),
             "completed_by": str(entry["completed_by"]) if entry.get("completed_by") else None}
            for entry in action_plan_payload
        ]

    poc.updated_by = user.user_id
    poc.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(poc)
    return poc


def _iso(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return value.isoformat()


@router.post("/{poc_id}/sign", response_model=BereavementPOCRead)
def sign_bereavement_poc(
    poc_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(BEREAVEMENT_EDIT_ROLES)),
):
    poc = _get_owned_poc(db, poc_id, user)
    get_authorized_patient(db, poc.patient_id, user)

    if poc.status == "SIGNED":
        raise HTTPException(status_code=409, detail="POC is already signed")

    poc.status = "SIGNED"
    poc.signed_by = user.user_id
    poc.signed_at = datetime.now(timezone.utc)
    poc.updated_by = user.user_id
    poc.updated_at = datetime.now(timezone.utc)

    audit_event(
        db=db,
        tenant_id=str(user.tenant_id),
        user_id=str(user.user_id),
        role=(user.role or "").strip().upper(),
        action="BEREAVEMENT_POC_SIGNED",
        entity_type="BEREAVEMENT_POC",
        entity_id=str(poc.id),
        meta={"patient_id": str(poc.patient_id), "risk_level": poc.risk_level},
    )

    db.commit()
    db.refresh(poc)
    return poc
