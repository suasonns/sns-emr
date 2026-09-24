from __future__ import annotations

"""
Clinical Outcome API (issue #143 API phase). Thin router over
app.services.clinical_outcome_service -- all business logic stays in the
service layer; this module only handles auth, tenant/patient/admission
validation, request/response shaping, and HTTP error mapping.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api._compliance_common import get_tenant_patient, require_clinical_outcome_role, resolve_actor
from app.core.database import get_db
from app.dependencies.auth import CurrentUser, get_current_user
from app.models.clinical_outcome import ClinicalOutcomeAuditEvent, ClinicalOutcomeRecord
from app.models.patient_response import PatientResponseEvent
from app.services import clinical_outcome_service as svc

router = APIRouter(tags=["Clinical Outcome"], dependencies=[Depends(require_clinical_outcome_role())])


# ---------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------


class ClinicalOutcomeCreate(BaseModel):
    patient_response_event_id: str
    source_task_id: str | None = None
    source_visit_id: str | None = None


class InterventionCreate(BaseModel):
    intervention_timely: bool | None = None
    notes: str | None = None


class PatientResponseCreate(BaseModel):
    patient_response_status: str
    response_recorded_at: datetime
    patient_appropriately_cared_for: bool | None = None
    remaining_need_identified: bool = False


class OutcomeStatusChange(BaseModel):
    new_status: str
    reason: str | None = None


class OutcomeCorrection(BaseModel):
    corrections: dict[str, Any]
    correction_reason: str


class OutcomeFinalize(BaseModel):
    closed_at: datetime | None = None


class OutcomeReopen(BaseModel):
    reopen_reason: str


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def _get_record(db: Session, tenant_id: str, outcome_id: str) -> ClinicalOutcomeRecord:
    # svc.get_outcome_record normalizes tenant_id via str() internally -- no
    # per-router conversion needed here.
    try:
        return svc.get_outcome_record(db, tenant_id=tenant_id, record_id=outcome_id)
    except svc.ClinicalOutcomeError:
        raise HTTPException(status_code=404, detail="Clinical outcome record not found")


def _serialize(record: ClinicalOutcomeRecord) -> dict:
    return {
        "id": str(record.id),
        "tenant_id": str(record.tenant_id),
        "patient_id": str(record.patient_id),
        "admission_id": str(record.admission_id) if record.admission_id else None,
        "benefit_period_id": str(record.benefit_period_id) if record.benefit_period_id else None,
        "patient_response_event_id": str(record.patient_response_event_id)
        if record.patient_response_event_id
        else None,
        "outcome_status": record.outcome_status,
        "patient_appropriately_cared_for": record.patient_appropriately_cared_for,
        "patient_response_status": record.patient_response_status,
        "remaining_need_identified": record.remaining_need_identified,
        "idg_communicated": record.idg_communicated,
        "idg_communicated_at": record.idg_communicated_at.isoformat() if record.idg_communicated_at else None,
        "intervention_timely": record.intervention_timely,
        "documentation_complete": record.documentation_complete,
        "idg_review_id": str(record.idg_review_id) if record.idg_review_id else None,
        "response_recorded_at": record.response_recorded_at.isoformat() if record.response_recorded_at else None,
        "closed_at": record.closed_at.isoformat() if record.closed_at else None,
        "closed_by": str(record.closed_by) if record.closed_by else None,
        "reopened_at": record.reopened_at.isoformat() if record.reopened_at else None,
        "reopen_reason": record.reopen_reason,
        "notes": record.notes,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "created_by": str(record.created_by) if record.created_by else None,
        "created_by_account_discipline": record.created_by_account_discipline,
    }


# ---------------------------------------------------------------------
# Create / retrieve
# ---------------------------------------------------------------------


@router.post("/clinical-outcomes", operation_id="CreateClinicalOutcome")
def create_clinical_outcome(
    payload: ClinicalOutcomeCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    tenant_id = current_user.tenant_id
    event = db.get(PatientResponseEvent, payload.patient_response_event_id)
    if event is None or str(event.tenant_id) != str(tenant_id):
        raise HTTPException(status_code=404, detail="Patient response event not found")

    # Idempotent creation: a record already linked to this source event is
    # returned as-is rather than duplicated.
    existing = (
        db.query(ClinicalOutcomeRecord)
        .filter(
            ClinicalOutcomeRecord.tenant_id == tenant_id,
            ClinicalOutcomeRecord.patient_response_event_id == event.id,
        )
        .first()
    )
    if existing is not None:
        return _serialize(existing)

    actor_user_id, discipline = resolve_actor(db, current_user)
    try:
        record = svc.create_outcome_from_patient_response_event(
            db,
            event=event,
            actor_user_id=actor_user_id,
            actor_account_discipline=discipline,
            source_task_id=payload.source_task_id,
            source_visit_id=payload.source_visit_id,
        )
    except svc.ClinicalOutcomeError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e))

    db.commit()
    db.refresh(record)
    return _serialize(record)


@router.get("/clinical-outcomes/{outcome_id}", operation_id="GetClinicalOutcome")
def get_clinical_outcome(
    outcome_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    record = _get_record(db, current_user.tenant_id, outcome_id)
    return _serialize(record)


@router.get("/patients/{patient_id}/clinical-outcomes", operation_id="ListPatientClinicalOutcomes")
def list_patient_clinical_outcomes(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    get_tenant_patient(db, current_user.tenant_id, patient_id)
    rows = (
        db.query(ClinicalOutcomeRecord)
        .filter(
            ClinicalOutcomeRecord.tenant_id == current_user.tenant_id,
            ClinicalOutcomeRecord.patient_id == patient_id,
        )
        .order_by(ClinicalOutcomeRecord.created_at.desc())
        .all()
    )
    return [_serialize(r) for r in rows]


# ---------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------


@router.post("/clinical-outcomes/{outcome_id}/interventions", operation_id="RecordClinicalOutcomeIntervention")
def record_intervention(
    outcome_id: str,
    payload: InterventionCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    record = _get_record(db, current_user.tenant_id, outcome_id)
    actor_user_id, discipline = resolve_actor(db, current_user)
    try:
        svc.record_intervention(
            db,
            record=record,
            intervention_timely=payload.intervention_timely,
            actor_user_id=actor_user_id,
            actor_account_discipline=discipline,
            notes=payload.notes,
        )
    except svc.ClinicalOutcomeError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e))
    db.commit()
    db.refresh(record)
    return _serialize(record)


@router.post("/clinical-outcomes/{outcome_id}/patient-response", operation_id="RecordClinicalOutcomePatientResponse")
def record_patient_response(
    outcome_id: str,
    payload: PatientResponseCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    record = _get_record(db, current_user.tenant_id, outcome_id)
    actor_user_id, discipline = resolve_actor(db, current_user)
    try:
        svc.record_patient_response(
            db,
            record=record,
            patient_response_status=payload.patient_response_status,
            response_recorded_at=payload.response_recorded_at,
            patient_appropriately_cared_for=payload.patient_appropriately_cared_for,
            remaining_need_identified=payload.remaining_need_identified,
            actor_user_id=actor_user_id,
            actor_account_discipline=discipline,
        )
    except svc.ClinicalOutcomeError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e))
    db.commit()
    db.refresh(record)
    return _serialize(record)


@router.post("/clinical-outcomes/{outcome_id}/status", operation_id="ChangeClinicalOutcomeStatus")
def change_outcome_status(
    outcome_id: str,
    payload: OutcomeStatusChange,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    record = _get_record(db, current_user.tenant_id, outcome_id)
    actor_user_id, discipline = resolve_actor(db, current_user)
    try:
        svc.change_outcome_status(
            db,
            record=record,
            new_status=payload.new_status,
            actor_user_id=actor_user_id,
            actor_account_discipline=discipline,
            reason=payload.reason,
        )
    except svc.ClinicalOutcomeError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e))
    db.commit()
    db.refresh(record)
    return _serialize(record)


@router.post("/clinical-outcomes/{outcome_id}/correct", operation_id="CorrectClinicalOutcome")
def correct_outcome(
    outcome_id: str,
    payload: OutcomeCorrection,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    record = _get_record(db, current_user.tenant_id, outcome_id)
    actor_user_id, discipline = resolve_actor(db, current_user)
    try:
        svc.correct_outcome(
            db,
            record=record,
            corrections=payload.corrections,
            correction_reason=payload.correction_reason,
            actor_user_id=actor_user_id,
            actor_account_discipline=discipline,
        )
    except svc.ClinicalOutcomeError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e))
    db.commit()
    db.refresh(record)
    return _serialize(record)


@router.post("/clinical-outcomes/{outcome_id}/finalize", operation_id="FinalizeClinicalOutcome")
def finalize_outcome(
    outcome_id: str,
    payload: OutcomeFinalize,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    record = _get_record(db, current_user.tenant_id, outcome_id)
    actor_user_id, discipline = resolve_actor(db, current_user)
    try:
        svc.finalize_outcome(
            db,
            record=record,
            closed_at=payload.closed_at or datetime.utcnow(),
            actor_user_id=actor_user_id,
            actor_account_discipline=discipline,
        )
    except svc.ClinicalOutcomeError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e))
    db.commit()
    db.refresh(record)
    return _serialize(record)


@router.post("/clinical-outcomes/{outcome_id}/reopen", operation_id="ReopenClinicalOutcome")
def reopen_outcome(
    outcome_id: str,
    payload: OutcomeReopen,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    record = _get_record(db, current_user.tenant_id, outcome_id)
    actor_user_id, discipline = resolve_actor(db, current_user)
    try:
        svc.reopen_outcome(
            db,
            record=record,
            reopen_reason=payload.reopen_reason,
            actor_user_id=actor_user_id,
            actor_account_discipline=discipline,
        )
    except svc.ClinicalOutcomeError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e))
    db.commit()
    db.refresh(record)
    return _serialize(record)


@router.get("/clinical-outcomes/{outcome_id}/audit", operation_id="GetClinicalOutcomeAudit")
def get_clinical_outcome_audit(
    outcome_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    record = _get_record(db, current_user.tenant_id, outcome_id)
    rows = (
        db.query(ClinicalOutcomeAuditEvent)
        .filter(
            ClinicalOutcomeAuditEvent.tenant_id == current_user.tenant_id,
            ClinicalOutcomeAuditEvent.clinical_outcome_record_id == record.id,
        )
        .order_by(ClinicalOutcomeAuditEvent.created_at.asc())
        .all()
    )
    return [
        {
            "id": str(r.id),
            "event_type": r.event_type,
            "actor_user_id": str(r.actor_user_id) if r.actor_user_id else None,
            "actor_account_discipline": r.actor_account_discipline,
            "prior_value": r.prior_value,
            "new_value": r.new_value,
            "reason": r.reason,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
