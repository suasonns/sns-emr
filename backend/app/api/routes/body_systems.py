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

Permission model: ordinary draft save/read deliberately reuses the SAME
pattern already used by RN ICA's own save/update/lock endpoints
(app/api/visits.py) -- tenant + care-team authorization via
`get_authorized_patient`, with NO separate per-action role allow-list.
RNICA's save/update/lock endpoints were inspected and confirmed to gate
access this same way (patient-access authorization only), so Body Systems
draft save follows the identical, already-established convention rather
than inventing a new role list.

Correction/amendment endpoints (added for compliance remediation blocker
A -- "never destroy, always append" correction history) are the one
exception: deciding (approve/deny) an amendment reuses the EXISTING
`AMENDMENT_APPROVAL_ROLES` role allow-list already governing RNICA
amendment decisions, imported directly from app/api/visits.py rather than
redefined, so the two workflows cannot silently drift apart on who may
decide a correction. See app/models/body_systems_amendment.py and
app/services/body_systems_amendment_service.py for the full design.

Audit: every save calls `app.services.audit_logger.log_event`, the same
non-blocking audit mechanism RNICA uses (`_safe_log_event` wraps it there;
this module calls it directly since Body Systems writes are not on an
error-sensitive hot path). Amendment submit/approve/deny calls
`app.services.audit_events.audit_event` (the same helper
`rnica_amendment_service.py` uses) so correction history is independently
auditable from ordinary draft saves.
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
# Reuses the SAME review-authority set that already governs RNICA amendment
# decisions (SECTION 12 Amendment Infrastructure) -- app/api/visits.py has
# no reference to this module, so importing from it here carries no
# circular-import risk. Imported directly rather than redefined so the two
# amendment workflows can never silently drift apart on who may approve/
# deny a correction.
from app.api.visits import AMENDMENT_APPROVAL_ROLES
from app.services.audit_events import audit_event
from app.services.audit_logger import log_event
from app.services.body_systems_amendment_service import (
    BodySystemsAmendmentError,
    approve_amendment,
    create_amendment,
    deny_amendment,
    list_amendments,
)

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


class BodySystemsAmendmentRequest(BaseModel):
    """A correction/amendment request against a system assessment. Never
    overwrites the original content -- see app/models/body_systems_amendment.py.
    """

    fieldReference: Optional[str] = None
    amendmentCategory: str
    reasonCode: str
    requestedChange: str
    requestSource: str = "STAFF"
    originalValueSnapshot: Optional[Any] = None
    proposedValue: Optional[Any] = None


class BodySystemsAmendmentDecisionRequest(BaseModel):
    decisionReason: Optional[str] = None


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

    # Draft-vs-authenticated boundary (compliance remediation blocker A).
    # `_get_or_create_current_assessment` already excludes "signed"
    # assessments from being reused as "current" -- a new draft row is
    # created instead, so a signed assessment's own system_assessments rows
    # are never reachable here at all. This additional check covers the
    # other non-draft statuses in ASSESSMENT_STATUSES ("ready_for_review",
    # "recorded"): once an assessment has left "draft", ordinary field
    # overwrite is rejected and the amendment workflow below
    # (POST .../correction-request) must be used instead. No route in this
    # milestone currently transitions status away from "draft", so this is
    # presently a dormant, forward-looking guard -- documented here rather
    # than silently omitted, per the project's own escape hatch for
    # draft-only features.
    if assessment.status != "draft":
        audit_event(
            db=db,
            action="body_systems.respiratory.direct_edit_rejected",
            entity_type="system_assessment",
            entity_id=str(system_assessment.id),
            user_id=_user_id(current_user),
            tenant_id=str(assessment.tenant_id),
            role=getattr(current_user, "role", None),
            meta={"patientId": str(patient_uuid), "assessmentStatus": assessment.status},
        )
        db.commit()
        raise HTTPException(
            status_code=409,
            detail=(
                "This Body Systems assessment has left draft status "
                f"(current status: {assessment.status!r}). Direct field edits are no longer "
                "permitted; submit a correction/amendment request instead."
            ),
        )

    responsible_clinician_id = _resolve_responsible_clinician(
        db, payload.limitationResponsibleClinicianId, patient.tenant_id
    )

    if payload.expectedVersion is not None and payload.expectedVersion != system_assessment.version:
        audit_event(
            db=db,
            action="body_systems.respiratory.stale_write_rejected",
            entity_type="system_assessment",
            entity_id=str(system_assessment.id),
            user_id=_user_id(current_user),
            tenant_id=str(assessment.tenant_id),
            role=getattr(current_user, "role", None),
            meta={
                "patientId": str(patient_uuid),
                "expectedVersion": payload.expectedVersion,
                "actualVersion": system_assessment.version,
            },
        )
        db.commit()
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


# ---------------------------------------------------------------------------
# Correction/amendment endpoints (compliance remediation blocker A).
#
# "Never destroy, always append": these endpoints never modify
# `system_assessments` rows directly. They create/decide
# `body_systems_amendments` rows that reference a system assessment by id,
# exactly mirroring the RNICA SECTION 12 amendment workflow
# (app/api/visits.py's /rnica/{assessment_id}/correction-request family).
# ---------------------------------------------------------------------------


def _resolve_system_assessment_or_404(db: Session, patient: Any, patient_uuid: uuid.UUID) -> SystemAssessment:
    assessment = _get_or_create_current_assessment(db, patient_uuid, patient.tenant_id)
    return _get_or_create_system_assessment(db, assessment, RESPIRATORY_SYSTEM)


@router.post("/patients/{patient_id}/respiratory/correction-request", status_code=201)
def submit_respiratory_amendment(
    patient_id: str,
    payload: BodySystemsAmendmentRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="patient_id must be a valid UUID") from None

    patient = get_authorized_patient(db, patient_uuid, current_user)
    system_assessment = _resolve_system_assessment_or_404(db, patient, patient_uuid)

    user_id = getattr(current_user, "user_id", None) or getattr(current_user, "id", None)

    try:
        record = create_amendment(
            db,
            tenant_id=patient.tenant_id,
            patient_id=patient_uuid,
            system_assessment_id=system_assessment.id,
            system=RESPIRATORY_SYSTEM,
            user_id=user_id,
            field_reference=payload.fieldReference,
            amendment_category=payload.amendmentCategory,
            reason_code=payload.reasonCode,
            requested_change=payload.requestedChange,
            request_source=payload.requestSource,
            original_value_snapshot=payload.originalValueSnapshot,
            proposed_value=payload.proposedValue,
        )
    except BodySystemsAmendmentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return record


@router.get("/patients/{patient_id}/respiratory/amendments")
def get_respiratory_amendments(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="patient_id must be a valid UUID") from None

    patient = get_authorized_patient(db, patient_uuid, current_user)
    system_assessment = _resolve_system_assessment_or_404(db, patient, patient_uuid)

    amendments = list_amendments(db, tenant_id=patient.tenant_id, system_assessment_id=system_assessment.id)
    return {"systemAssessmentId": str(system_assessment.id), "amendments": amendments}


def _require_amendment_decision_role(current_user: CurrentUser) -> None:
    # Same normalization RNICA's approve/deny endpoints apply before
    # comparing against AMENDMENT_APPROVAL_ROLES (app/api/visits.py).
    actor_role = str(getattr(current_user, "role", "SYSTEM") or "SYSTEM").strip().upper()
    if actor_role not in AMENDMENT_APPROVAL_ROLES:
        raise HTTPException(
            status_code=403,
            detail="DPCS, DPCS Designee, Case Manager, or Supervisor approval is required to decide an amendment.",
        )


@router.post("/patients/{patient_id}/respiratory/amendments/{amendment_id}/approve")
def approve_respiratory_amendment(
    patient_id: str,
    amendment_id: str,
    payload: BodySystemsAmendmentDecisionRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="patient_id must be a valid UUID") from None

    patient = get_authorized_patient(db, patient_uuid, current_user)
    _require_amendment_decision_role(current_user)

    try:
        amendment_uuid = uuid.UUID(amendment_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="amendment_id must be a valid UUID") from None

    user_id = getattr(current_user, "user_id", None) or getattr(current_user, "id", None)
    try:
        return approve_amendment(
            db,
            tenant_id=patient.tenant_id,
            amendment_id=amendment_uuid,
            user_id=user_id,
            decision_reason=payload.decisionReason,
        )
    except BodySystemsAmendmentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/patients/{patient_id}/respiratory/amendments/{amendment_id}/deny")
def deny_respiratory_amendment(
    patient_id: str,
    amendment_id: str,
    payload: BodySystemsAmendmentDecisionRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="patient_id must be a valid UUID") from None

    patient = get_authorized_patient(db, patient_uuid, current_user)
    _require_amendment_decision_role(current_user)

    try:
        amendment_uuid = uuid.UUID(amendment_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="amendment_id must be a valid UUID") from None

    if not payload.decisionReason or not payload.decisionReason.strip():
        raise HTTPException(status_code=422, detail="decisionReason is required to deny an amendment")

    user_id = getattr(current_user, "user_id", None) or getattr(current_user, "id", None)
    try:
        return deny_amendment(
            db,
            tenant_id=patient.tenant_id,
            amendment_id=amendment_uuid,
            user_id=user_id,
            decision_reason=payload.decisionReason,
        )
    except BodySystemsAmendmentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

