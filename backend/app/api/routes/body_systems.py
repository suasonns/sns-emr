"""Body Systems — Respiratory API endpoints (live RNICA mount).

Backs the frontend Respiratory panel (sns-emr-frontend/src/domain/body-systems
/respiratoryFieldInventory.ts, respiratoryWorkflowRules.ts) with real
persistence (app/models/body_systems.py). Situation classification and
exception derivation remain the frontend domain layer's primary
responsibility (respiratoryWorkflowRules.ts is the single source of truth
for that business logic); the backend persists what the client computed
but additionally enforces (see `_assert_completion_is_not_forged` below)
that a REVIEWED/REVIEWED_WITH_EXCEPTION reviewState cannot be reached
without the same required-field invariants the frontend enforces -- a
client cannot bypass completion requirements merely by sending the
end-state string.

Episode/RNICA scoping: every route is scoped by `{assessment_id}`, the
SAME `RnicaAssessment.id` identity `/rnica/{assessment_id}` in
app/api/visits.py already authorizes on. A patient-only lookup cannot
distinguish two RNICA episodes for the same patient; this module never
falls back to a patient-only "most recent" query.

Permission model: deliberately reuses the SAME pattern already used by RN
ICA's own save/update/lock endpoints (app/api/visits.py) -- tenant +
care-team authorization via `get_authorized_patient`, with NO separate
per-action role allow-list. RNICA's save/update/lock endpoints were
inspected and confirmed to gate access this same way (patient-access
authorization only), so Body Systems draft save follows the identical,
already-established convention rather than inventing a new role list (the
ORDER_SIGNER_ROLES / AMENDMENT_APPROVAL_ROLES precedent found elsewhere in
the codebase gates a different, narrower class of action -- physician
order signature and amendment approval -- not routine clinical
documentation saves).

Audit: every save calls `app.services.audit_logger.log_event`, the same
non-blocking audit mechanism RNICA uses (`_safe_log_event` wraps it there;
this module calls it directly since Body Systems writes are not on an
error-sensitive hot path). The audit actor is always derived from the
authenticated `current_user`, never from the client payload.
"""
from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Security
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.patient_access import get_authorized_patient
from app.core.security import CurrentUser, get_current_user
from app.models.body_systems import (
    ASSESSMENT_SITUATIONS,
    BodySystemsAssessment,
    EXCEPTION_BLOCKING_LEVELS,
    EXCEPTION_TYPES,
    REVIEW_STATES,
    ReviewException,
    SystemAssessment,
)
from app.models.rnica_assessment import RnicaAssessment
from app.services.audit_logger import log_event

router = APIRouter(prefix="/visits/body-systems", tags=["body-systems"])

RESPIRATORY_SYSTEM = "respiratory"

# ---------------------------------------------------------------------------
# Server-side completion safety (cannot be forged by the client).
#
# Ports the SAME blocking requirement logic as
# sns-emr-frontend/src/domain/body-systems/respiratoryWorkflowRules.ts
# (getSatisfiedRespiratoryRequirementKeys / stateMachine.ts
# SITUATION_REQUIREMENTS), restricted to the subset of requirement keys
# that module treats as record-blocking (i.e. NOT in
# RESPIRATORY_NOT_VERIFIED_REQUIREMENTS, which remain informational-only
# on both sides). If the frontend's requirement graph changes, this must
# be updated to match -- the two are intentionally kept in lockstep rather
# than only existing on the client.
# ---------------------------------------------------------------------------

_CLINICAL_STATUS_CHANGE_WORSENING = {"Declining", "New Symptom Since Prior Assessment"}


def _has_any_current_finding_field(data: dict[str, Any]) -> bool:
    oxygen = data.get("oxygenTherapy") or {}
    ventilator = data.get("ventilator") or {}
    return bool(
        data.get("sobSeverity")
        or data.get("exertionLevel")
        or (data.get("lungSounds") or [])
        or (data.get("respirations") or [])
        or data.get("coughType")
        or data.get("sputumCharacter")
        or (isinstance(oxygen, dict) and oxygen.get("inUse"))
        or (isinstance(ventilator, dict) and ventilator.get("shortTermVentilator"))
        or (isinstance(ventilator, dict) and ventilator.get("longTermVentilator"))
    )


def _has_documented_intervention_or_response(data: dict[str, Any]) -> bool:
    oxygen = data.get("oxygenTherapy") or {}
    ventilator = data.get("ventilator") or {}
    return bool(
        data.get("treatmentInitiated") is True
        or data.get("treatmentDeclined") is True
        or (isinstance(oxygen, dict) and oxygen.get("inUse") is True)
        or (isinstance(ventilator, dict) and ventilator.get("shortTermVentilator") is True)
        or (isinstance(ventilator, dict) and ventilator.get("longTermVentilator") is True)
    )


def _has_documented_current_finding_or_change(data: dict[str, Any]) -> bool:
    change = data.get("clinicalStatusChange")
    return bool(change in _CLINICAL_STATUS_CHANGE_WORSENING or _has_any_current_finding_field(data))


def _has_documented_unable_to_assess_reason(data: dict[str, Any]) -> bool:
    reason = data.get("respiratoryUnableToAssessReason")
    if not reason:
        return False
    if reason == "Other":
        other = data.get("respiratoryUnableToAssessOther")
        return bool(other and str(other).strip())
    return True


def _missing_blocking_respiratory_requirements(situation: Optional[str], data: dict[str, Any]) -> list[str]:
    """Returns the record-blocking requirement keys still missing for
    `situation`. An empty list means the blocking requirements for that
    situation are satisfied (informational-only requirements -- e.g.
    `dated_prior_reference`, `follow_up_decision`, `scope`,
    `assessed_portion_if_any`, `follow_up_responsibility`,
    `timing_or_contingency` -- are intentionally never included here;
    they cannot block completion on either side of the stack)."""
    if situation == "no_current_concern":
        return []
    if situation == "stable_existing":
        satisfied = _has_any_current_finding_field(data) or bool(data.get("clinicalStatusChange"))
        return [] if satisfied else ["current_confirmation"]
    if situation == "new_or_worsening":
        missing: list[str] = []
        if not _has_documented_current_finding_or_change(data):
            missing.append("current_finding_or_change")
        if not _has_documented_intervention_or_response(data):
            missing.append("intervention_or_response")
        return missing
    if situation == "unable_to_assess":
        return [] if _has_documented_unable_to_assess_reason(data) else ["reason"]
    return ["situation"]


def _assert_completion_is_not_forged(
    review_state: str, situation: Optional[str], data: dict[str, Any], exceptions: list["ReviewExceptionIn"]
) -> None:
    """Raises 422 if `review_state` claims REVIEWED/REVIEWED_WITH_EXCEPTION
    without the data to back it up. Draft saves (not_reviewed/in_progress)
    are never subject to this check -- per spec, draft save must remain
    available when incomplete."""
    if review_state not in ("reviewed", "reviewed_with_exception"):
        return
    if situation is None:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Cannot complete review: no situation could be derived from the entered data.",
                "missingRequirements": ["situation"],
            },
        )
    missing = _missing_blocking_respiratory_requirements(situation, data)
    if missing:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Cannot complete review: required fields are missing.",
                "missingRequirements": missing,
            },
        )
    has_open_record_blocking = any(exception.blockingLevel == "record_blocking" for exception in exceptions)
    if review_state == "reviewed" and has_open_record_blocking:
        raise HTTPException(
            status_code=422,
            detail={
                "message": (
                    "Cannot mark REVIEWED while record-blocking exceptions are open; "
                    "use reviewState=reviewed_with_exception instead."
                ),
                "missingRequirements": [],
            },
        )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ReviewExceptionIn(BaseModel):
    type: str
    message: str
    blockingLevel: str
    fieldPath: Optional[str] = None


class SaveRespiratoryDraftRequest(BaseModel):
    situation: Optional[str] = None
    data: dict[str, Any] = Field(default_factory=dict)
    summary: Optional[str] = None
    reviewState: str = "in_progress"
    reviewExceptions: list[ReviewExceptionIn] = Field(default_factory=list)
    # Optimistic concurrency (spec section 12): the client must send back
    # the version it last read. A mismatch means someone else saved in
    # between -- reject rather than silently overwrite their write.
    expectedVersion: Optional[int] = None


def _user_id(current_user: CurrentUser) -> Optional[str]:
    raw = getattr(current_user, "user_id", None) or getattr(current_user, "id", None)
    return str(raw) if raw else None


def _get_authorized_rnica_assessment(db: Session, assessment_id: uuid.UUID, current_user: CurrentUser):
    """Looks up the RNICA episode by id (the SAME identity
    `/rnica/{assessment_id}` already authorizes on in app/api/visits.py),
    then authorizes the caller against its patient via the shared
    `get_authorized_patient` helper -- the exact convention every other
    patient-scoped router in this codebase follows. 404s rather than 403s
    when the assessment_id does not exist at all, matching the existing
    `/rnica/{assessment_id}` routes' behavior, so a guess of a nonexistent
    id cannot be distinguished from a real-but-unauthorized one by response
    code alone (both are rejected; only the message differs for debugging)."""
    record = db.query(RnicaAssessment).filter(RnicaAssessment.id == assessment_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="RNICA assessment not found")
    patient = get_authorized_patient(db, record.patient_id, current_user)
    return record, patient


def _get_or_create_current_assessment(
    db: Session, patient_id: uuid.UUID, tenant_id: uuid.UUID, rnica_assessment_id: uuid.UUID
) -> BodySystemsAssessment:
    """Returns the Body Systems assessment for THIS SPECIFIC RNICA episode
    (`rnica_assessment_id`), creating a fresh draft if none exists yet.
    Episode-scoped, NOT patient-scoped: two RNICA episodes for the same
    patient never share or collide with each other's Body Systems record.
    """
    assessment = (
        db.query(BodySystemsAssessment)
        .filter(
            BodySystemsAssessment.rnica_assessment_id == rnica_assessment_id,
            BodySystemsAssessment.patient_id == patient_id,
            BodySystemsAssessment.tenant_id == tenant_id,
        )
        .order_by(BodySystemsAssessment.started_at.desc())
        .first()
    )
    if assessment is not None:
        return assessment

    assessment = BodySystemsAssessment(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        rnica_assessment_id=rnica_assessment_id,
        visit_mode="routine_rn",
        status="draft",
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


def _get_or_create_system_assessment(
    db: Session, assessment: BodySystemsAssessment, system: str
) -> SystemAssessment:
    system_assessment = (
        db.query(SystemAssessment)
        .filter(
            SystemAssessment.body_systems_assessment_id == assessment.id,
            SystemAssessment.system == system,
        )
        .first()
    )
    if system_assessment is not None:
        return system_assessment

    system_assessment = SystemAssessment(
        id=uuid.uuid4(),
        tenant_id=assessment.tenant_id,
        body_systems_assessment_id=assessment.id,
        system=system,
    )
    db.add(system_assessment)
    db.commit()
    db.refresh(system_assessment)
    return system_assessment


def _serialize_system_assessment(system_assessment: SystemAssessment, open_exceptions: list[ReviewException]) -> dict:
    return {
        "id": str(system_assessment.id),
        "bodySystemsAssessmentId": str(system_assessment.body_systems_assessment_id),
        "system": system_assessment.system,
        "situation": system_assessment.situation,
        "reviewState": system_assessment.review_state,
        "data": dict(system_assessment.data or {}),
        "summary": system_assessment.summary,
        "version": system_assessment.version,
        "updatedAt": system_assessment.updated_at.isoformat() if system_assessment.updated_at else None,
        "openReviewExceptions": [
            {
                "id": str(exception.id),
                "type": exception.type,
                "message": exception.message,
                "blockingLevel": exception.blocking_level,
                "fieldPath": exception.field_path,
            }
            for exception in open_exceptions
        ],
    }


def _open_exceptions_for(db: Session, assessment_id: uuid.UUID, system: str) -> list[ReviewException]:
    return (
        db.query(ReviewException)
        .filter(
            ReviewException.body_systems_assessment_id == assessment_id,
            ReviewException.system == system,
            ReviewException.status == "open",
        )
        .all()
    )


@router.get("/rnica/{assessment_id}/respiratory")
def get_current_respiratory_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    try:
        assessment_uuid = uuid.UUID(assessment_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="assessment_id must be a valid UUID") from None

    rnica_record, patient = _get_authorized_rnica_assessment(db, assessment_uuid, current_user)
    assessment = _get_or_create_current_assessment(db, patient.id, patient.tenant_id, assessment_uuid)
    system_assessment = _get_or_create_system_assessment(db, assessment, RESPIRATORY_SYSTEM)
    open_exceptions = _open_exceptions_for(db, assessment.id, RESPIRATORY_SYSTEM)

    return {
        "bodySystemsAssessmentId": str(assessment.id),
        "rnicaAssessmentId": str(rnica_record.id),
        "assessmentStatus": assessment.status,
        **_serialize_system_assessment(system_assessment, open_exceptions),
    }


@router.put("/rnica/{assessment_id}/respiratory")
def save_respiratory_draft(
    assessment_id: str,
    payload: SaveRespiratoryDraftRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    try:
        assessment_uuid = uuid.UUID(assessment_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="assessment_id must be a valid UUID") from None

    if payload.situation is not None and payload.situation not in ASSESSMENT_SITUATIONS:
        raise HTTPException(status_code=422, detail=f"situation must be one of {ASSESSMENT_SITUATIONS}")
    if payload.reviewState not in REVIEW_STATES:
        raise HTTPException(status_code=422, detail=f"reviewState must be one of {REVIEW_STATES}")
    for exception_in in payload.reviewExceptions:
        if exception_in.type not in EXCEPTION_TYPES:
            raise HTTPException(status_code=422, detail=f"reviewExceptions[].type must be one of {EXCEPTION_TYPES}")
        if exception_in.blockingLevel not in EXCEPTION_BLOCKING_LEVELS:
            raise HTTPException(
                status_code=422,
                detail=f"reviewExceptions[].blockingLevel must be one of {EXCEPTION_BLOCKING_LEVELS}",
            )

    # Anti-forgery: a client cannot reach REVIEWED/REVIEWED_WITH_EXCEPTION
    # merely by sending that string -- the data must actually back it up.
    _assert_completion_is_not_forged(payload.reviewState, payload.situation, payload.data, payload.reviewExceptions)

    rnica_record, patient = _get_authorized_rnica_assessment(db, assessment_uuid, current_user)

    if rnica_record.status == "LOCKED":
        raise HTTPException(
            status_code=409,
            detail="This RNICA assessment is already locked/signed; Body Systems can no longer be modified.",
        )

    assessment = _get_or_create_current_assessment(db, patient.id, patient.tenant_id, assessment_uuid)
    system_assessment = _get_or_create_system_assessment(db, assessment, RESPIRATORY_SYSTEM)

    if payload.expectedVersion is not None and payload.expectedVersion != system_assessment.version:
        raise HTTPException(
            status_code=409,
            detail=(
                "This Respiratory assessment was updated by someone else since you last loaded it. "
                "Reload the latest version before saving again."
            ),
        )

    system_assessment.situation = payload.situation
    system_assessment.data = dict(payload.data)
    system_assessment.summary = payload.summary
    system_assessment.review_state = payload.reviewState
    system_assessment.version = (system_assessment.version or 1) + 1
    system_assessment.assessed_by = (
        uuid.UUID(str(getattr(current_user, "user_id", None) or getattr(current_user, "id", None)))
        if (getattr(current_user, "user_id", None) or getattr(current_user, "id", None))
        else None
    )

    # Replace the auto-derived OPEN exception set for this system with what
    # the client computed (respiratoryWorkflowRules.buildRespiratoryExceptions).
    # Exceptions a clinician has already resolved/waived are left untouched --
    # only ones still "open" are superseded by a fresh save.
    previously_open = _open_exceptions_for(db, assessment.id, RESPIRATORY_SYSTEM)
    for exception in previously_open:
        db.delete(exception)
    for incoming in payload.reviewExceptions:
        db.add(
            ReviewException(
                id=uuid.uuid4(),
                tenant_id=assessment.tenant_id,
                body_systems_assessment_id=assessment.id,
                system=RESPIRATORY_SYSTEM,
                type=incoming.type,
                field_path=incoming.fieldPath,
                message=incoming.message,
                blocking_level=incoming.blockingLevel,
                status="open",
            )
        )

    db.commit()
    db.refresh(system_assessment)

    db.info["tenant_id"] = str(assessment.tenant_id)
    log_event(
        user_id=_user_id(current_user),
        tenant_id=str(assessment.tenant_id),
        role=getattr(current_user, "role", None),
        action="body_systems.respiratory.save_draft",
        entity_type="system_assessment",
        entity_id=str(system_assessment.id),
        metadata={
            "patientId": str(patient.id),
            "rnicaAssessmentId": str(rnica_record.id),
            "bodySystemsAssessmentId": str(assessment.id),
            "situation": system_assessment.situation,
            "reviewState": system_assessment.review_state,
            "openExceptionCount": len(payload.reviewExceptions),
        },
        db=db,
    )

    open_exceptions = _open_exceptions_for(db, assessment.id, RESPIRATORY_SYSTEM)
    return {
        "bodySystemsAssessmentId": str(assessment.id),
        "rnicaAssessmentId": str(rnica_record.id),
        "assessmentStatus": assessment.status,
        **_serialize_system_assessment(system_assessment, open_exceptions),
    }
