"""Generic FacesheetFieldSuggestion review/apply API.

This is the missing half of the "harvest -> suggestion queue -> review ->
apply" loop identified in docs/architecture/InsuranceMappingReconciliation.md.
The write/queue half already existed (app/api/patients.py::
_reconcile_demographic_field, called from persist_patient_from_hnp_extraction);
this module builds the review/apply half, generically, for EVERY
suggestible field (demographic today, insurance as of this change, any
future OCR/AI-sourced field without further API changes) -- not an
insurance-specific endpoint.

SSOT contract (see docs/workflows/SourceOfTruthMatrix.md):
  - FacesheetFieldSuggestion is a staging/candidate queue only. It is
    NEVER read by any consumer (billing, claims, readiness) as
    authoritative.
  - PatientFaceSheet remains the sole source of truth. A suggestion only
    affects PatientFaceSheet when a human explicitly accepts it via this
    API -- there is no automatic write path here.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.patient_access import get_authorized_patient
from app.db_tenant_dependency import get_db_tenant
from app.models.facesheet_field_suggestion import (
    FACESHEET_SUGGESTIBLE_FIELDS,
    FacesheetFieldSuggestion,
)
from app.models.patient_facesheet import PatientFaceSheet
from app.services.audit_events import audit_event

from app.api.patients import require_tenant_user, _tenant_id_uuid

router = APIRouter(prefix="/field-suggestions", tags=["field-suggestions"])

# Suggestions in these statuses may still be actioned by a reviewer.
_ACTIONABLE_STATUSES = ("pending", "auto_applied")


class FieldSuggestionResponse(BaseModel):
    id: str
    patient_id: str
    field_name: str
    current_value: str | None
    suggested_value: str | None
    source_document_id: str | None
    status: str
    created_at: datetime | None
    resolved_at: datetime | None

    class Config:
        from_attributes = True


def _serialize(row: FacesheetFieldSuggestion) -> FieldSuggestionResponse:
    return FieldSuggestionResponse(
        id=str(row.id),
        patient_id=str(row.patient_id),
        field_name=row.field_name,
        current_value=row.current_value,
        suggested_value=row.suggested_value,
        source_document_id=str(row.source_document_id) if row.source_document_id else None,
        status=row.status,
        created_at=row.created_at,
        resolved_at=row.resolved_at,
    )


def _get_suggestion(
    db: Session, *, tenant_id: uuid.UUID, suggestion_id: uuid.UUID
) -> FacesheetFieldSuggestion:
    row = (
        db.query(FacesheetFieldSuggestion)
        .filter(
            FacesheetFieldSuggestion.id == suggestion_id,
            FacesheetFieldSuggestion.tenant_id == tenant_id,
        )
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Field suggestion not found")
    return row


def _coerce_value(field_name: str, raw_value: str | None):
    value_type = FACESHEET_SUGGESTIBLE_FIELDS.get(field_name, "string")
    if raw_value is None:
        return None
    if value_type == "date":
        return date.fromisoformat(raw_value)
    return raw_value


@router.get("", response_model=list[FieldSuggestionResponse])
def list_field_suggestions(
    patient_id: uuid.UUID = Query(...),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db_tenant),
    user=Depends(require_tenant_user),
):
    """List field suggestions for a patient. Defaults to actionable
    (pending/auto_applied) suggestions only; pass status= to filter to a
    specific status, including resolved ones for audit/history review."""
    tenant_id = _tenant_id_uuid(user)
    get_authorized_patient(db, patient_id, user)

    q = db.query(FacesheetFieldSuggestion).filter(
        FacesheetFieldSuggestion.tenant_id == tenant_id,
        FacesheetFieldSuggestion.patient_id == patient_id,
    )
    if status:
        q = q.filter(FacesheetFieldSuggestion.status == status)
    else:
        q = q.filter(FacesheetFieldSuggestion.status.in_(_ACTIONABLE_STATUSES))

    rows = q.order_by(FacesheetFieldSuggestion.created_at.desc()).all()
    return [_serialize(r) for r in rows]


@router.post("/{suggestion_id}/accept", response_model=FieldSuggestionResponse)
def accept_field_suggestion(
    suggestion_id: uuid.UUID,
    db: Session = Depends(get_db_tenant),
    user=Depends(require_tenant_user),
):
    """Accept a suggestion: write suggested_value onto PatientFaceSheet
    (the SSOT) and mark the suggestion resolved. If the suggestion was
    already auto-applied (WARN mode), the value is already on
    PatientFaceSheet -- this simply acknowledges/resolves the record
    without re-writing it."""
    tenant_id = _tenant_id_uuid(user)
    user_id = getattr(user, "user_id", None)
    row = _get_suggestion(db, tenant_id=tenant_id, suggestion_id=suggestion_id)
    get_authorized_patient(db, row.patient_id, user)

    if row.status not in _ACTIONABLE_STATUSES:
        raise HTTPException(
            status_code=409,
            detail=f"Suggestion already resolved (status={row.status})",
        )

    if row.status == "pending":
        facesheet = (
            db.query(PatientFaceSheet)
            .filter(
                PatientFaceSheet.tenant_id == tenant_id,
                PatientFaceSheet.patient_id == row.patient_id,
            )
            .first()
        )
        if facesheet is None:
            raise HTTPException(status_code=404, detail="Facesheet not found for patient")

        if row.field_name not in FACESHEET_SUGGESTIBLE_FIELDS:
            raise HTTPException(
                status_code=422,
                detail=f"Field '{row.field_name}' is not a recognized suggestible field",
            )

        setattr(facesheet, row.field_name, _coerce_value(row.field_name, row.suggested_value))
        facesheet.updated_by = user_id
        facesheet.updated_at = datetime.now(timezone.utc)

    row.status = "accepted"
    row.resolved_at = datetime.now(timezone.utc)
    row.resolved_by = user_id

    audit_event(
        db=db,
        action="facesheet_field_suggestion_accepted",
        entity_type="patient_facesheet",
        entity_id=str(row.patient_id),
        user_id=str(user_id) if user_id else None,
        tenant_id=str(tenant_id),
        meta={
            "field_name": row.field_name,
            "previous_value": row.current_value,
            "applied_value": row.suggested_value,
            "source_document_id": str(row.source_document_id) if row.source_document_id else None,
            "suggestion_id": str(row.id),
        },
    )

    db.commit()
    db.refresh(row)
    return _serialize(row)


@router.post("/{suggestion_id}/reject", response_model=FieldSuggestionResponse)
def reject_field_suggestion(
    suggestion_id: uuid.UUID,
    db: Session = Depends(get_db_tenant),
    user=Depends(require_tenant_user),
):
    """Reject a pending suggestion: PatientFaceSheet is left untouched.
    Not available for auto_applied rows (the value is already live on
    PatientFaceSheet under WARN mode; use the facesheet edit endpoint
    directly to correct it, which will itself queue any new conflict)."""
    tenant_id = _tenant_id_uuid(user)
    user_id = getattr(user, "user_id", None)
    row = _get_suggestion(db, tenant_id=tenant_id, suggestion_id=suggestion_id)
    get_authorized_patient(db, row.patient_id, user)

    if row.status != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"Only pending suggestions can be rejected (status={row.status})",
        )

    row.status = "rejected"
    row.resolved_at = datetime.now(timezone.utc)
    row.resolved_by = user_id

    audit_event(
        db=db,
        action="facesheet_field_suggestion_rejected",
        entity_type="patient_facesheet",
        entity_id=str(row.patient_id),
        user_id=str(user_id) if user_id else None,
        tenant_id=str(tenant_id),
        meta={
            "field_name": row.field_name,
            "current_value": row.current_value,
            "rejected_value": row.suggested_value,
            "source_document_id": str(row.source_document_id) if row.source_document_id else None,
            "suggestion_id": str(row.id),
        },
    )

    db.commit()
    db.refresh(row)
    return _serialize(row)


@router.post("/{suggestion_id}/dismiss", response_model=FieldSuggestionResponse)
def dismiss_field_suggestion(
    suggestion_id: uuid.UUID,
    db: Session = Depends(get_db_tenant),
    user=Depends(require_tenant_user),
):
    """Dismiss a suggestion (pending or auto_applied) as not actionable
    (e.g. duplicate, unrelated document, known-bad OCR read) without
    accepting or rejecting it as a correction decision. PatientFaceSheet
    is never modified by this action."""
    tenant_id = _tenant_id_uuid(user)
    user_id = getattr(user, "user_id", None)
    row = _get_suggestion(db, tenant_id=tenant_id, suggestion_id=suggestion_id)
    get_authorized_patient(db, row.patient_id, user)

    if row.status not in _ACTIONABLE_STATUSES:
        raise HTTPException(
            status_code=409,
            detail=f"Suggestion already resolved (status={row.status})",
        )

    row.status = "dismissed"
    row.resolved_at = datetime.now(timezone.utc)
    row.resolved_by = user_id

    audit_event(
        db=db,
        action="facesheet_field_suggestion_dismissed",
        entity_type="patient_facesheet",
        entity_id=str(row.patient_id),
        user_id=str(user_id) if user_id else None,
        tenant_id=str(tenant_id),
        meta={
            "field_name": row.field_name,
            "suggested_value": row.suggested_value,
            "source_document_id": str(row.source_document_id) if row.source_document_id else None,
            "suggestion_id": str(row.id),
        },
    )

    db.commit()
    db.refresh(row)
    return _serialize(row)
