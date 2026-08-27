# api/bereavement_letters.py

"""
Bereavement Letters Tracker API -- fourth of five planned Bereavement
sub-sections (see chart-section-bereavement-letters,
models/bereavement_letter_tracker.py).

Tracks the CMS COP 418.64(d) 13-month post-death bereavement contact
schedule per bereaved contact: what touchpoint is due, when, whether it was
completed, by whom, and how -- with tenant-wide overdue/due-soon alerting
so follow-up is never missed. Unlike the Bereavement POC/Post-Death
Assessment, this record is never signature-locked: individual touchpoints
must stay completable for the full 13 months, long after any linked POC has
been signed. Only whole-tracker discontinuation (e.g. family opts out) is
tracked explicitly.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.patient_access import get_authorized_patient
from app.core.permissions import require_roles
from app.core.security import CurrentUser
from app.models.bereavement_assessment import BereavementAssessment
from app.models.bereavement_letter_tracker import BereavementLetterTracker
from app.models.bereavement_poc import BereavementPOC
from app.models.patient import Patient
from app.models.patient_facesheet import PatientFaceSheet
from app.services.audit_events import audit_event
from app.services.bereavement_letters_service import (
    DUE_SOON_WINDOW_DAYS,
    build_default_items,
    item_runtime_status,
    serialize_items_with_status,
    summarize_items,
)

router = APIRouter(prefix="/bereavement-letters", tags=["bereavement"])

BEREAVEMENT_VIEW_ROLES = ["LVN", "RN", "NP", "PA", "MD", "MSW", "SC", "Chaplain", "CHHA", "Surveyor"]
BEREAVEMENT_EDIT_ROLES = ["MSW", "SC", "Chaplain", "RN", "NP", "PA", "MD"]

SENT_METHODS = {"MAIL", "EMAIL", "PHONE", "IN_PERSON", "OTHER"}
TRACKER_STATUSES = {"ACTIVE", "COMPLETE", "DISCONTINUED"}


class BereavementLetterTrackerCreate(BaseModel):
    patient_id: uuid.UUID
    bereavement_poc_id: uuid.UUID | None = None
    bereavement_assessment_id: uuid.UUID | None = None
    date_of_death: date | None = None
    risk_level: str | None = None


class BereavementLetterTrackerUpdate(BaseModel):
    status: str | None = None
    discontinued_reason: str | None = None
    date_of_death: date | None = None
    risk_level: str | None = None
    # Re-seed items from the (possibly updated) schedule inputs while
    # preserving any already-completed items by key. Defaults to False so a
    # plain status/date edit never silently touches the checklist.
    resync_schedule: bool = False


class BereavementLetterItemUpdate(BaseModel):
    included: bool | None = None
    due_date: date | None = None
    sent_date: date | None = None
    sent_method: str | None = None
    notes: str | None = None
    # Explicitly clear a previously-recorded completion (e.g. logged in
    # error) -- distinct from simply omitting sent_date, which leaves it
    # untouched.
    clear_sent: bool = False


class BereavementLetterTrackerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    patient_id: uuid.UUID
    bereavement_poc_id: uuid.UUID | None = None
    bereavement_assessment_id: uuid.UUID | None = None
    date_of_death: date | None = None
    risk_level: str | None = None
    status: str
    discontinued_reason: str | None = None
    discontinued_at: datetime | None = None
    discontinued_by: uuid.UUID | None = None
    items: list[dict]
    summary: dict
    created_by: uuid.UUID
    created_at: datetime
    updated_by: uuid.UUID | None = None
    updated_at: datetime | None = None


def _resolve_linked(db: Session, user: CurrentUser, patient_id: uuid.UUID, poc_id, assessment_id):
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

    return linked_poc, linked_assessment


def _get_owned(db: Session, tracker_id: uuid.UUID, user: CurrentUser) -> BereavementLetterTracker:
    tracker = (
        db.query(BereavementLetterTracker)
        .filter(
            BereavementLetterTracker.id == tracker_id,
            BereavementLetterTracker.tenant_id == user.tenant_id,
        )
        .one_or_none()
    )
    if tracker is None:
        raise HTTPException(status_code=404, detail="Bereavement letters tracker not found")
    return tracker


def _serialize(tracker: BereavementLetterTracker) -> dict:
    today = datetime.now(timezone.utc).date()
    items = serialize_items_with_status(tracker.items or [], today)
    return {
        "id": tracker.id,
        "tenant_id": tracker.tenant_id,
        "patient_id": tracker.patient_id,
        "bereavement_poc_id": tracker.bereavement_poc_id,
        "bereavement_assessment_id": tracker.bereavement_assessment_id,
        "date_of_death": tracker.date_of_death,
        "risk_level": tracker.risk_level,
        "status": tracker.status,
        "discontinued_reason": tracker.discontinued_reason,
        "discontinued_at": tracker.discontinued_at,
        "discontinued_by": tracker.discontinued_by,
        "items": items,
        "summary": summarize_items(tracker.items or [], today),
        "created_by": tracker.created_by,
        "created_at": tracker.created_at,
        "updated_by": tracker.updated_by,
        "updated_at": tracker.updated_at,
    }


@router.post("", response_model=BereavementLetterTrackerRead, status_code=status.HTTP_201_CREATED)
def create_bereavement_letter_tracker(
    payload: BereavementLetterTrackerCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(BEREAVEMENT_EDIT_ROLES)),
):
    patient = get_authorized_patient(db, payload.patient_id, user)

    linked_poc, linked_assessment = _resolve_linked(
        db, user, patient.id, payload.bereavement_poc_id, payload.bereavement_assessment_id
    )

    date_of_death = payload.date_of_death or (linked_poc.date_of_death if linked_poc else None)
    risk_level = payload.risk_level or (linked_poc.risk_level if linked_poc else None) or (
        linked_assessment.risk_level if linked_assessment else None
    )

    tracker = BereavementLetterTracker(
        tenant_id=patient.tenant_id,
        patient_id=patient.id,
        bereavement_poc_id=payload.bereavement_poc_id,
        bereavement_assessment_id=payload.bereavement_assessment_id,
        date_of_death=date_of_death,
        risk_level=risk_level,
        items=build_default_items(risk_level, date_of_death),
        created_by=user.user_id,
    )

    db.add(tracker)
    db.flush()

    audit_event(
        db=db,
        tenant_id=str(user.tenant_id),
        user_id=str(user.user_id),
        role=(user.role or "").strip().upper(),
        action="BEREAVEMENT_LETTER_TRACKER_CREATED",
        entity_type="BEREAVEMENT_LETTER_TRACKER",
        entity_id=str(tracker.id),
        meta={"patient_id": str(tracker.patient_id), "risk_level": tracker.risk_level},
    )

    db.commit()
    db.refresh(tracker)
    return _serialize(tracker)


@router.get("/patient/{patient_id}", response_model=list[BereavementLetterTrackerRead])
def list_bereavement_letter_trackers(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(BEREAVEMENT_VIEW_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)
    trackers = (
        db.query(BereavementLetterTracker)
        .filter(
            BereavementLetterTracker.tenant_id == patient.tenant_id,
            BereavementLetterTracker.patient_id == patient.id,
        )
        .order_by(BereavementLetterTracker.created_at.desc())
        .all()
    )
    return [_serialize(t) for t in trackers]


@router.get("/{tracker_id}", response_model=BereavementLetterTrackerRead)
def get_bereavement_letter_tracker(
    tracker_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(BEREAVEMENT_VIEW_ROLES)),
):
    tracker = _get_owned(db, tracker_id, user)
    get_authorized_patient(db, tracker.patient_id, user)
    return _serialize(tracker)


@router.patch("/{tracker_id}", response_model=BereavementLetterTrackerRead)
def update_bereavement_letter_tracker(
    tracker_id: uuid.UUID,
    payload: BereavementLetterTrackerUpdate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(BEREAVEMENT_EDIT_ROLES)),
):
    tracker = _get_owned(db, tracker_id, user)
    get_authorized_patient(db, tracker.patient_id, user)

    changes = payload.model_dump(exclude_unset=True, exclude={"resync_schedule"})

    if "status" in changes and changes["status"] not in TRACKER_STATUSES:
        raise HTTPException(status_code=400, detail=f"status must be one of {sorted(TRACKER_STATUSES)}")

    date_of_death_changed = "date_of_death" in changes
    risk_level_changed = "risk_level" in changes

    for field_name, value in changes.items():
        setattr(tracker, field_name, value)

    if changes.get("status") == "DISCONTINUED":
        tracker.discontinued_at = datetime.now(timezone.utc)
        tracker.discontinued_by = user.user_id
    elif changes.get("status") in ("ACTIVE", "COMPLETE"):
        tracker.discontinued_at = None
        tracker.discontinued_by = None
        if changes.get("status") == "ACTIVE":
            tracker.discontinued_reason = None

    if payload.resync_schedule and (date_of_death_changed or risk_level_changed):
        completed_by_key = {
            item["key"]: item
            for item in (tracker.items or [])
            if item.get("sent_date")
        }
        fresh_items = build_default_items(tracker.risk_level, tracker.date_of_death)
        for item in fresh_items:
            prior = completed_by_key.get(item["key"])
            if prior:
                item["sent_date"] = prior.get("sent_date")
                item["sent_method"] = prior.get("sent_method")
                item["sent_by"] = prior.get("sent_by")
                item["notes"] = prior.get("notes")
        tracker.items = fresh_items

        audit_event(
            db=db,
            tenant_id=str(user.tenant_id),
            user_id=str(user.user_id),
            role=(user.role or "").strip().upper(),
            action="BEREAVEMENT_LETTER_TRACKER_RESYNCED",
            entity_type="BEREAVEMENT_LETTER_TRACKER",
            entity_id=str(tracker.id),
            meta={"patient_id": str(tracker.patient_id)},
        )

    tracker.updated_by = user.user_id
    tracker.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(tracker)
    return _serialize(tracker)


@router.patch("/{tracker_id}/items/{item_key}", response_model=BereavementLetterTrackerRead)
def update_bereavement_letter_item(
    tracker_id: uuid.UUID,
    item_key: str,
    payload: BereavementLetterItemUpdate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(BEREAVEMENT_EDIT_ROLES)),
):
    tracker = _get_owned(db, tracker_id, user)
    get_authorized_patient(db, tracker.patient_id, user)

    if payload.sent_method is not None and payload.sent_method not in SENT_METHODS:
        raise HTTPException(status_code=400, detail=f"sent_method must be one of {sorted(SENT_METHODS)}")

    items = list(tracker.items or [])
    idx = next((i for i, it in enumerate(items) if it.get("key") == item_key), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Touchpoint item not found on this tracker")

    item = dict(items[idx])
    changes = payload.model_dump(exclude_unset=True, exclude={"clear_sent"})

    if payload.clear_sent:
        item["sent_date"] = None
        item["sent_method"] = None
        item["sent_by"] = None
        changes.pop("sent_date", None)
        changes.pop("sent_method", None)

    if "included" in changes:
        item["included"] = changes["included"]
    if "due_date" in changes:
        item["due_date"] = changes["due_date"].isoformat() if changes["due_date"] else None
    if "notes" in changes:
        item["notes"] = changes["notes"]
    if "sent_date" in changes:
        item["sent_date"] = changes["sent_date"].isoformat() if changes["sent_date"] else None
        item["sent_by"] = str(user.user_id) if item["sent_date"] else None
    if "sent_method" in changes:
        item["sent_method"] = changes["sent_method"]

    items[idx] = item
    tracker.items = items
    tracker.updated_by = user.user_id
    tracker.updated_at = datetime.now(timezone.utc)

    # Auto-mark the whole tracker COMPLETE once every active (included)
    # touchpoint has been sent -- surfaces completion without requiring a
    # separate manual step, while still leaving the record open to
    # DISCONTINUED/manual edits later if something needs correcting.
    summary = summarize_items(items)
    if summary["complete"] and tracker.status == "ACTIVE":
        tracker.status = "COMPLETE"

    audit_event(
        db=db,
        tenant_id=str(user.tenant_id),
        user_id=str(user.user_id),
        role=(user.role or "").strip().upper(),
        action="BEREAVEMENT_LETTER_ITEM_UPDATED",
        entity_type="BEREAVEMENT_LETTER_TRACKER",
        entity_id=str(tracker.id),
        meta={"patient_id": str(tracker.patient_id), "item_key": item_key, "sent": bool(item.get("sent_date"))},
    )

    db.commit()
    db.refresh(tracker)
    return _serialize(tracker)


@router.get("/alerts/overdue")
def get_bereavement_letter_alerts(
    within_days: int = Query(default=DUE_SOON_WINDOW_DAYS, ge=0, le=90),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(BEREAVEMENT_VIEW_ROLES)),
):
    """
    Tenant-wide overdue / due-soon bereavement touchpoint alerts, flattened
    across every ACTIVE tracker -- the dashboard-facing replacement for
    manually flipping through the paper bereavement binder. Respects the
    same care-team scoping as everything else: a non-full-access clinician
    only sees alerts for patients they're authorized to access.
    """
    today = datetime.now(timezone.utc).date()

    trackers = (
        db.query(BereavementLetterTracker, Patient, PatientFaceSheet)
        .join(Patient, Patient.id == BereavementLetterTracker.patient_id)
        .outerjoin(PatientFaceSheet, PatientFaceSheet.patient_id == Patient.id)
        .filter(
            BereavementLetterTracker.tenant_id == user.tenant_id,
            BereavementLetterTracker.status == "ACTIVE",
        )
        .all()
    )

    overdue: list[dict] = []
    due_soon: list[dict] = []

    for tracker, patient, facesheet in trackers:
        # Enforce care-team scoping per-patient rather than a single
        # tenant-wide query short-circuit, matching get_authorized_patient's
        # rules (full-access roles / assigned patients / unclaimed
        # caseload).
        try:
            get_authorized_patient(db, patient.id, user)
        except HTTPException:
            continue

        patient_name = " ".join(
            part for part in [facesheet.first_name if facesheet else None, facesheet.last_name if facesheet else None] if part
        ).strip() or None

        for item in tracker.items or []:
            item_status = item_runtime_status(item, today)
            if item_status not in ("OVERDUE", "DUE_SOON"):
                continue
            due_raw = item.get("due_date")
            due = due_raw if isinstance(due_raw, date) else (date.fromisoformat(due_raw) if due_raw else None)
            if item_status == "DUE_SOON" and due and (due - today).days > within_days:
                continue

            entry = {
                "tracker_id": tracker.id,
                "patient_id": patient.id,
                "patient_name": patient_name,
                "item_key": item.get("key"),
                "label": item.get("label"),
                "contact_type": item.get("contact_type"),
                "due_date": item.get("due_date"),
                "days_overdue": (today - due).days if item_status == "OVERDUE" and due else None,
                "days_until_due": (due - today).days if item_status == "DUE_SOON" and due else None,
                "risk_level": tracker.risk_level,
            }
            (overdue if item_status == "OVERDUE" else due_soon).append(entry)

    overdue.sort(key=lambda e: e["days_overdue"] or 0, reverse=True)
    due_soon.sort(key=lambda e: e["days_until_due"] or 0)

    return {
        "as_of": today.isoformat(),
        "within_days": within_days,
        "overdue_count": len(overdue),
        "due_soon_count": len(due_soon),
        "overdue": overdue,
        "due_soon": due_soon,
    }
