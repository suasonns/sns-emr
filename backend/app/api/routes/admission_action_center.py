# app/api/routes/admission_action_center.py
"""Admission Action Center (Phase A) routes.

Global, RN-ICA-reachable request/status tracker (Medication Request,
Physician Order, DME Order, Supply Order, Referral). Mounted under the
same `/visits/rnica/{assessment_id}` prefix as the POC control routes so
the frontend can open it as a modal/drawer from any RN ICA section without
navigating away or losing draft state, while every request stays traceable
back to the RN ICA assessment/section that raised it.

Deliberately NOT lock-gated: Admission Action Center is a cross-cutting
operational workflow (per the frozen master map's Action Center framing)
available independent of assessment completion/lock status.
"""

from __future__ import annotations

import datetime as _dt
import uuid

from fastapi import APIRouter, Depends, HTTPException, Security
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import get_current_user, CurrentUser
from app.services import admission_action_center_service as service
from app.api.routes.rnica_poc import (
    _load_assessment_and_authorize,
    _tenant_id_for,
    _user_id,
)

router = APIRouter(prefix="/visits/rnica", tags=["admission-action-center"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class CreateActionRequest(BaseModel):
    request_type: str = Field(..., min_length=1)
    details: str = Field(..., min_length=1)
    source_section: str | None = None
    responsible_discipline: str | None = None
    priority: str | None = None
    required_by_date: str | None = None
    type_details: dict | None = None
    plan_of_care_version_id: str | None = None


class UpdateActionStatusRequest(BaseModel):
    status: str = Field(..., min_length=1)
    note: str | None = None


class CompleteActionRequest(BaseModel):
    completion_evidence: str = Field(..., min_length=1)
    note: str | None = None


class CancelActionRequest(BaseModel):
    cancellation_reason: str = Field(..., min_length=1)


@router.get("/{assessment_id}/action-center")
def list_action_center_requests(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    """Returns every Admission Action Center request for this patient
    (not just those raised from the current assessment), so the drawer
    always shows the full picture regardless of which section it's opened
    from.
    """
    record = _load_assessment_and_authorize(db, assessment_id, current_user)
    tenant_id = _tenant_id_for(db, record)

    requests = service.list_requests(db, tenant_id=tenant_id, patient_id=record.patient_id)
    return {"assessmentId": str(record.id), "requests": requests}


@router.post("/{assessment_id}/action-center", status_code=201)
def create_action_center_request(
    assessment_id: str,
    payload: CreateActionRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    record = _load_assessment_and_authorize(db, assessment_id, current_user)
    tenant_id = _tenant_id_for(db, record)
    if tenant_id is None:
        raise HTTPException(status_code=400, detail="Patient has no tenant assigned")

    try:
        result = service.create_request(
            db,
            tenant_id=tenant_id,
            patient_id=record.patient_id,
            user_id=_user_id(current_user),
            request_type=payload.request_type,
            details=payload.details,
            rnica_assessment_id=record.id,
            source_section=payload.source_section,
            responsible_discipline=payload.responsible_discipline,
            priority=payload.priority,
            required_by_date=(
                _dt.date.fromisoformat(payload.required_by_date)
                if payload.required_by_date
                else None
            ),
            type_details=payload.type_details,
            plan_of_care_version_id=payload.plan_of_care_version_id,
        )
    except service.AdmissionActionCenterError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return {"assessmentId": str(record.id), **result}


@router.post("/{assessment_id}/action-center/{request_id}/complete")
def complete_action_center_request(
    assessment_id: str,
    request_id: str,
    payload: CompleteActionRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    record = _load_assessment_and_authorize(db, assessment_id, current_user)
    tenant_id = _tenant_id_for(db, record)

    try:
        request_uuid = uuid.UUID(request_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="request_id must be a valid UUID") from None

    try:
        result = service.complete_request(
            db,
            tenant_id=tenant_id,
            request_id=request_uuid,
            user_id=_user_id(current_user),
            completion_evidence=payload.completion_evidence,
            note=payload.note,
        )
    except service.AdmissionActionCenterError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(e)) from e

    return {"assessmentId": str(record.id), **result}


@router.post("/{assessment_id}/action-center/{request_id}/cancel")
def cancel_action_center_request(
    assessment_id: str,
    request_id: str,
    payload: CancelActionRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    record = _load_assessment_and_authorize(db, assessment_id, current_user)
    tenant_id = _tenant_id_for(db, record)

    try:
        request_uuid = uuid.UUID(request_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="request_id must be a valid UUID") from None

    try:
        result = service.cancel_request(
            db,
            tenant_id=tenant_id,
            request_id=request_uuid,
            user_id=_user_id(current_user),
            cancellation_reason=payload.cancellation_reason,
        )
    except service.AdmissionActionCenterError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(e)) from e

    return {"assessmentId": str(record.id), **result}


@router.patch("/{assessment_id}/action-center/{request_id}/status")
def update_action_center_request_status(
    assessment_id: str,
    request_id: str,
    payload: UpdateActionStatusRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Security(get_current_user),
):
    record = _load_assessment_and_authorize(db, assessment_id, current_user)
    tenant_id = _tenant_id_for(db, record)

    try:
        request_uuid = uuid.UUID(request_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="request_id must be a valid UUID") from None

    try:
        result = service.update_status(
            db,
            tenant_id=tenant_id,
            request_id=request_uuid,
            user_id=_user_id(current_user),
            new_status=payload.status,
            note=payload.note,
        )
    except service.AdmissionActionCenterError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(e)) from e

    return {"assessmentId": str(record.id), **result}
