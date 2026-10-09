"""Body Systems — Respiratory proof-of-pattern API endpoints.

Backs the Body Systems Workspace's approved `RespiratorySystemPanel.tsx`
(sns-emr-frontend/src/features/body-systems-workspace/systems/respiratory/)
with real persistence (app/models/body_systems.py). Intentionally minimal
for the proof-of-pattern milestone: find-or-create the current draft
assessment, and save it. Situation classification and exception derivation
remain the frontend domain layer's responsibility; the backend persists
whatever the client computed and enforces only structural/concurrency/
authorization rules. The frontend's single source of truth for that mapping
is `respiratoryPersistenceMapping.ts` (Workspace-scoped, typed) -- the
earlier `respiratoryWorkflowRules.ts` it might otherwise reference was a
different, HOPE-worktree implementation that was deliberately not imported
into this integration branch; it never shipped here.

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
error-sensitive hot path).
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
from app.models.user import User
from app.services.audit_logger import log_event

router = APIRouter(prefix="/visits/body-systems", tags=["body-systems"])

RESPIRATORY_SYSTEM = "respiratory"


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
    # Unable-to-Assess limitation sub-fields (AssessmentLimitation, spec
    # section 4.2). All six now have a backend destination
    # (system_assessments.limitation_* -- see c3b1d9e0f4a7 for the two
    # added in Phase F1) -- see respiratoryPersistenceMapping.ts for the
    # authoritative field-by-field classification.
    limitationScope: Optional[list[str]] = None
    limitationReason: Optional[str] = None
    limitationAssessedPortion: Optional[str] = None
    limitationFollowUpRequired: Optional[bool] = None
    limitationResponsibleClinicianId: Optional[str] = None
    limitationTimingOrContingency: Optional[str] = None
    # Optimistic concurrency (spec section 12): the client must send back
    # the version it last read. A mismatch means someone else saved in
    # between -- reject rather than silently overwrite their write.
    expectedVersion: Optional[int] = None


def _user_id(current_user: CurrentUser) -> Optional[str]:
    raw = getattr(current_user, "user_id", None) or getattr(current_user, "id", None)
    return str(raw) if raw else None


def _get_or_create_current_assessment(db: Session, patient_id: uuid.UUID, tenant_id: uuid.UUID) -> BodySystemsAssessment:
    """Returns the patient's most recent non-signed Body Systems assessment,
    creating a fresh draft if none exists yet. A patient has at most one
    "current" (not yet signed) assessment at a time for this proof-of-pattern
    milestone -- once signed, the next save starts a new one.
    """
    assessment = (
        db.query(BodySystemsAssessment)
        .filter(
            BodySystemsAssessment.patient_id == patient_id,
            BodySystemsAssessment.tenant_id == tenant_id,
            BodySystemsAssessment.status != "signed",
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
        "limitationScope": list(system_assessment.limitation_scope) if system_assessment.limitation_scope else None,
        "limitationReason": system_assessment.limitation_reason,
        "limitationAssessedPortion": system_assessment.limitation_assessed_portion,
        "limitationFollowUpRequired": (
            _text_to_bool(system_assessment.limitation_follow_up_required)
            if system_assessment.limitation_follow_up_required is not None
            else None
        ),
        "limitationResponsibleClinicianId": (
            str(system_assessment.limitation_responsible_clinician_id)
            if system_assessment.limitation_responsible_clinician_id
            else None
        ),
        "limitationTimingOrContingency": system_assessment.limitation_timing_or_contingency,
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


def _text_to_bool(value: str) -> bool:
    """Reversible string<->bool transform for `limitation_follow_up_required`
    (a Text column, not Boolean -- see app/models/body_systems.py). Stores
    exactly "true"/"false"; any other stored value is a data error, not a
    silent default, so it raises rather than guessing.
    """
    if value == "true":
        return True
    if value == "false":
        return False
    raise ValueError(f"Unexpected limitation_follow_up_required value: {value!r}")


def _resolve_responsible_clinician(db: Session, raw_id: Optional[str], tenant_id: uuid.UUID) -> Optional[uuid.UUID]:
    """Validates `limitationResponsibleClinicianId` before it is persisted.

    Unlike assessed_by/recorded_by/signed_by (always the current authenticated
    user), this field lets a clinician assign follow-up to a DIFFERENT staff
    member, so it must be independently validated: malformed UUID, unknown
    user, or cross-tenant reference are all rejected with the same 422 (not
    distinguished, so a caller cannot use this endpoint to probe which user
    IDs exist in another tenant).
    """
    if raw_id is None:
        return None
    try:
        clinician_uuid = uuid.UUID(raw_id)
    except ValueError:
        raise HTTPException(
            status_code=422, detail="limitationResponsibleClinicianId must be a valid UUID"
        ) from None

    clinician = (
        db.query(User)
        .filter(User.id == clinician_uuid, User.tenant_id == tenant_id)
        .first()
    )
    if clinician is None:
        raise HTTPException(
            status_code=422,
            detail="limitationResponsibleClinicianId must reference an existing clinician in this tenant",
        )
    return clinician_uuid


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


@router.get("/patients/{patient_id}/respiratory")
def get_current_respiratory_assessment(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="patient_id must be a valid UUID") from None

    patient = get_authorized_patient(db, patient_uuid, current_user)
    assessment = _get_or_create_current_assessment(db, patient_uuid, patient.tenant_id)
    system_assessment = _get_or_create_system_assessment(db, assessment, RESPIRATORY_SYSTEM)
    open_exceptions = _open_exceptions_for(db, assessment.id, RESPIRATORY_SYSTEM)

    return {
        "bodySystemsAssessmentId": str(assessment.id),
        "assessmentStatus": assessment.status,
        **_serialize_system_assessment(system_assessment, open_exceptions),
    }


@router.put("/patients/{patient_id}/respiratory")
def save_respiratory_draft(
    patient_id: str,
    payload: SaveRespiratoryDraftRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="patient_id must be a valid UUID") from None

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

    patient = get_authorized_patient(db, patient_uuid, current_user)
    assessment = _get_or_create_current_assessment(db, patient_uuid, patient.tenant_id)
    system_assessment = _get_or_create_system_assessment(db, assessment, RESPIRATORY_SYSTEM)

    responsible_clinician_id = _resolve_responsible_clinician(
        db, payload.limitationResponsibleClinicianId, patient.tenant_id
    )

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
    system_assessment.limitation_scope = list(payload.limitationScope) if payload.limitationScope is not None else None
    system_assessment.limitation_reason = payload.limitationReason
    system_assessment.limitation_assessed_portion = payload.limitationAssessedPortion
    system_assessment.limitation_follow_up_required = (
        ("true" if payload.limitationFollowUpRequired else "false")
        if payload.limitationFollowUpRequired is not None
        else None
    )
    system_assessment.limitation_responsible_clinician_id = responsible_clinician_id
    system_assessment.limitation_timing_or_contingency = payload.limitationTimingOrContingency
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
            "patientId": str(patient_uuid),
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
        "assessmentStatus": assessment.status,
        **_serialize_system_assessment(system_assessment, open_exceptions),
    }
