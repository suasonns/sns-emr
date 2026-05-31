from __future__ import annotations

from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db_tenant_dependency import get_db_tenant
from app.core.security import get_current_user
from app.services.audit_logger import log_event

from app.services.admission_authorization_service import (
    record_records_release_consent,
    authorize_admission,
)

router = APIRouter(prefix="/admissions", tags=["admissions"])


class RecordsReleaseRequest(BaseModel):
    signed_at: datetime = Field(..., json_schema_extra={"example": "2026-05-29T12:00:00Z"})


class AuthorizeAdmissionRequest(BaseModel):
    election_signed_at: datetime = Field(..., json_schema_extra={"example": "2026-05-29T14:00:00Z"})


@router.post("/{patient_id}/records-release", status_code=status.HTTP_200_OK)
def records_release(
    patient_id: uuid.UUID,
    payload: RecordsReleaseRequest,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    patient = record_records_release_consent(
        db,
        patient_id=patient_id,
        signed_at=payload.signed_at,
        user_id=user.id,
    )

    log_event(
        user_id=user.id,
        role=(user.role or "").upper(),
        action="RECORDS_RELEASE_SIGNED",
        entity_type="patient",
        entity_id=str(patient.id),
        db=db,
    )

    db.commit()
    return {"patient_id": str(patient.id), "admission_status": patient.admission_status}


@router.post("/{patient_id}/authorize", status_code=status.HTTP_200_OK)
def authorize(
    patient_id: uuid.UUID,
    payload: AuthorizeAdmissionRequest,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    patient = authorize_admission(
        db,
        patient_id=patient_id,
        election_signed_at=payload.election_signed_at,
        authorized_by_user_id=user.id,
    )

    log_event(
        user_id=user.id,
        role=(user.role or "").upper(),
        action="AUTHORIZE_ADMISSION",
        entity_type="patient",
        entity_id=str(patient.id),
        db=db,
    )

    db.commit()
    return {
        "patient_id": str(patient.id),
        "admission_status": patient.admission_status,
        "soc_date": patient.soc_date.isoformat() if patient.soc_date else None,
    }