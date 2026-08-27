# api/bereavement_support.py

"""
Post-Death Bereavement Support API -- fifth and final planned Bereavement
sub-section (see chart-section-bereavement-support).

Combines, for a single screen, everything a bereavement coordinator needs to
run ongoing post-death support without the paper binder:

  * A read-only **summary** of who the plan is for (primary bereaved contact),
    the death facts, and the current goals/interventions -- sourced from
    whichever of the Post-Death Bereavement Assessment / Bereavement POC has
    the information, so staff never have to re-key it here.
  * A **calendar** feed of every scheduled follow-up touchpoint (driven off
    BereavementLetterTracker.items, the single source of truth for the
    13-month CMS COP 418.64(d) schedule) for month-view, risk-color-coded
    rendering.
  * An append-only **communication note log** -- the automated replacement
    for the binder's handwritten contact log -- recording every phone call,
    visit, letter, or email exchanged with the bereaved family, whether or
    not it maps to a scheduled touchpoint.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.patient_access import get_authorized_patient
from app.core.permissions import require_roles
from app.core.security import CurrentUser
from app.models.bereavement_communication_note import BereavementCommunicationNote
from app.models.bereavement_letter_tracker import BereavementLetterTracker
from app.models.bereavement_poc import BereavementPOC
from app.models.post_death_bereavement_assessment import PostDeathBereavementAssessment
from app.services.audit_events import audit_event
from app.services.bereavement_letters_service import item_runtime_status

router = APIRouter(prefix="/bereavement-support", tags=["bereavement"])

BEREAVEMENT_VIEW_ROLES = ["LVN", "RN", "NP", "PA", "MD", "MSW", "SC", "Chaplain", "CHHA", "Surveyor"]
BEREAVEMENT_EDIT_ROLES = ["MSW", "SC", "Chaplain", "RN", "NP", "PA", "MD"]

CONTACT_TYPES = {"PHONE", "VISIT", "LETTER", "EMAIL", "OTHER"}

_PRIMARY_FIELDS = [
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

_DEATH_FACT_FIELDS = [
    "date_of_death",
    "place_of_death",
    "death_expected",
    "pcg_present_at_death",
    "family_present_at_death",
    "funeral_plans_finalized",
    "funeral_home_name",
]


class CommunicationNoteCreate(BaseModel):
    contact_date: date
    contact_type: str
    contact_with: str | None = None
    summary: str
    bereavement_letter_tracker_id: uuid.UUID | None = None


class CommunicationNoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    patient_id: uuid.UUID
    bereavement_letter_tracker_id: uuid.UUID | None = None
    contact_date: date
    contact_type: str
    contact_with: str | None = None
    summary: str
    created_by: uuid.UUID
    created_at: datetime


def _has_any(obj, fields: list[str]) -> bool:
    return any(getattr(obj, f, None) not in (None, "") for f in fields)


@router.get("/patient/{patient_id}/summary")
def get_bereavement_support_summary(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(BEREAVEMENT_VIEW_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)

    assessment = (
        db.query(PostDeathBereavementAssessment)
        .filter(
            PostDeathBereavementAssessment.tenant_id == patient.tenant_id,
            PostDeathBereavementAssessment.patient_id == patient.id,
        )
        .order_by(PostDeathBereavementAssessment.created_at.desc())
        .first()
    )
    poc = (
        db.query(BereavementPOC)
        .filter(
            BereavementPOC.tenant_id == patient.tenant_id,
            BereavementPOC.patient_id == patient.id,
        )
        .order_by(BereavementPOC.created_at.desc())
        .first()
    )

    # Primary bereaved / risk level / goals: prefer the Post-Death Assessment
    # (most recent, post-death) when it actually has the data, else fall
    # back to the POC so the screen is never blank just because no
    # Post-Death Assessment has been started yet.
    primary_source = assessment if assessment and _has_any(assessment, _PRIMARY_FIELDS) else poc
    goals_source = assessment if assessment and (assessment.goals or assessment.interventions) else poc

    primary_bereaved = (
        {field: getattr(primary_source, field) for field in _PRIMARY_FIELDS} if primary_source else None
    )
    death_facts = (
        {field: getattr(assessment, field) for field in _DEATH_FACT_FIELDS} if assessment else None
    )
    risk_level = (assessment.risk_level if assessment else None) or (poc.risk_level if poc else None)

    return {
        "patient_id": patient.id,
        "primary_bereaved": primary_bereaved,
        "death_facts": death_facts,
        "risk_level": risk_level,
        "goals": (goals_source.goals if goals_source else []) or [],
        "interventions": (goals_source.interventions if goals_source else []) or [],
        "other_interventions": goals_source.other_interventions if goals_source else None,
        "source_post_death_assessment_id": assessment.id if assessment else None,
        "source_bereavement_poc_id": poc.id if poc else None,
    }


@router.get("/patient/{patient_id}/calendar")
def get_bereavement_support_calendar(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(BEREAVEMENT_VIEW_ROLES)),
):
    """
    Flattened, risk-annotated feed of every scheduled bereavement touchpoint
    for this patient (across all non-discontinued trackers), for month-view
    calendar rendering. Each entry carries the tracker's risk_level so the UI
    can color-code LOW/MODERATE/HIGH without a second lookup.
    """
    patient = get_authorized_patient(db, patient_id, user)
    today = datetime.now(timezone.utc).date()

    trackers = (
        db.query(BereavementLetterTracker)
        .filter(
            BereavementLetterTracker.tenant_id == patient.tenant_id,
            BereavementLetterTracker.patient_id == patient.id,
            BereavementLetterTracker.status != "DISCONTINUED",
        )
        .all()
    )

    events: list[dict] = []
    for tracker in trackers:
        for item in tracker.items or []:
            if not item.get("due_date"):
                continue
            events.append(
                {
                    "tracker_id": tracker.id,
                    "item_key": item.get("key"),
                    "label": item.get("label"),
                    "contact_type": item.get("contact_type"),
                    "due_date": item.get("due_date"),
                    "risk_level": tracker.risk_level,
                    "status": item_runtime_status(item, today),
                    "included": item.get("included", True),
                }
            )

    events.sort(key=lambda e: e["due_date"] or "")
    return {"patient_id": patient.id, "events": events}


@router.post("/patient/{patient_id}/notes", response_model=CommunicationNoteRead, status_code=status.HTTP_201_CREATED)
def create_bereavement_communication_note(
    patient_id: uuid.UUID,
    payload: CommunicationNoteCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(BEREAVEMENT_EDIT_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)

    if payload.contact_type not in CONTACT_TYPES:
        raise HTTPException(status_code=400, detail=f"contact_type must be one of {sorted(CONTACT_TYPES)}")

    if payload.bereavement_letter_tracker_id is not None:
        tracker = (
            db.query(BereavementLetterTracker)
            .filter(
                BereavementLetterTracker.id == payload.bereavement_letter_tracker_id,
                BereavementLetterTracker.tenant_id == patient.tenant_id,
                BereavementLetterTracker.patient_id == patient.id,
            )
            .one_or_none()
        )
        if tracker is None:
            raise HTTPException(status_code=404, detail="Linked bereavement letters tracker not found")

    note = BereavementCommunicationNote(
        tenant_id=patient.tenant_id,
        patient_id=patient.id,
        bereavement_letter_tracker_id=payload.bereavement_letter_tracker_id,
        contact_date=payload.contact_date,
        contact_type=payload.contact_type,
        contact_with=payload.contact_with,
        summary=payload.summary,
        created_by=user.user_id,
    )
    db.add(note)
    db.flush()

    audit_event(
        db=db,
        tenant_id=str(user.tenant_id),
        user_id=str(user.user_id),
        role=(user.role or "").strip().upper(),
        action="BEREAVEMENT_COMMUNICATION_NOTE_CREATED",
        entity_type="BEREAVEMENT_COMMUNICATION_NOTE",
        entity_id=str(note.id),
        meta={"patient_id": str(note.patient_id), "contact_type": note.contact_type},
    )

    db.commit()
    db.refresh(note)
    return note


@router.get("/patient/{patient_id}/notes", response_model=list[CommunicationNoteRead])
def list_bereavement_communication_notes(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(BEREAVEMENT_VIEW_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)
    notes = (
        db.query(BereavementCommunicationNote)
        .filter(
            BereavementCommunicationNote.tenant_id == patient.tenant_id,
            BereavementCommunicationNote.patient_id == patient.id,
        )
        .order_by(BereavementCommunicationNote.contact_date.desc(), BereavementCommunicationNote.created_at.desc())
        .all()
    )
    return notes
