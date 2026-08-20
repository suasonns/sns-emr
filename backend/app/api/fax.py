# app/api/fax.py

"""
Fax endpoints for hospice orders (physician orders, comfort packs, DME/
supply requests) — matches HospiceMD's "Fax Order/History" workflow, backed
by the pluggable fax_service (SIMULATED provider today, real gateway later).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import CurrentUser
from app.core.database import get_db
from app.core.permissions import require_roles
from app.core.patient_access import get_authorized_patient
from app.models.patient import Patient
from app.models.fax_log import FaxLog
from app.services.fax_service import send_fax

router = APIRouter(prefix="/fax", tags=["fax"])

CLINICAL_ROLES = ["LVN", "RN", "NP", "MD", "Surveyor"]

SUBJECT_TYPES = {"MEDICATION", "PATIENT_ORDER", "ORDER_SET"}


class FaxSendRequest(BaseModel):
    subject_type: str
    subject_id: uuid.UUID | None = None
    recipient_name: str
    recipient_fax_number: str
    document_summary: str


def _serialize(fax: FaxLog) -> dict:
    return {
        "id": str(fax.id),
        "patient_id": str(fax.patient_id),
        "subject_type": fax.subject_type,
        "subject_id": str(fax.subject_id) if fax.subject_id else None,
        "recipient_name": fax.recipient_name,
        "recipient_fax_number": fax.recipient_fax_number,
        "status": fax.status,
        "provider": fax.provider,
        "provider_reference": fax.provider_reference,
        "document_summary": fax.document_summary,
        "failure_reason": fax.failure_reason,
        "sent_at": fax.sent_at.isoformat() if fax.sent_at else None,
        "created_at": fax.created_at.isoformat() if fax.created_at else None,
    }


@router.post("/patients/{patient_id}/send", summary="Queue/send a fax of an order, medication, or order set")
def queue_fax(
    patient_id: uuid.UUID,
    payload: FaxSendRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)

    subject_type = (payload.subject_type or "").strip().upper()
    if subject_type not in SUBJECT_TYPES:
        raise HTTPException(status_code=422, detail=f"subject_type must be one of {sorted(SUBJECT_TYPES)}")

    fax = send_fax(
        db,
        tenant_id=user.tenant_id,
        patient_id=patient_id,
        subject_type=subject_type,
        subject_id=payload.subject_id,
        recipient_name=payload.recipient_name,
        recipient_fax_number=payload.recipient_fax_number,
        document_summary=payload.document_summary,
        created_by=user.user_id,
    )
    return _serialize(fax)


@router.get("/patients/{patient_id}/history", summary="Fax Order/History — all faxes sent for a patient")
def fax_history(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    patient = get_authorized_patient(db, patient_id, user)

    faxes = (
        db.query(FaxLog)
        .filter(FaxLog.patient_id == patient_id, FaxLog.tenant_id == user.tenant_id)
        .order_by(FaxLog.created_at.desc())
        .all()
    )
    return [_serialize(f) for f in faxes]
