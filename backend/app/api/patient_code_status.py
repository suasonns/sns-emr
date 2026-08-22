# app/api/patient_code_status.py

"""
Structured, audited code-status (resuscitation directive) management.

Authoritative record consumed by Facesheet, RNICA, ACP/consent, Care
Overview, and Orders so a patient's Full Code / DNR / DNI / Comfort
Measures Only status can never disagree between modules. Every change is
appended as a new row so there is a permanent audit trail; exactly one row
per patient is is_current = true at any moment.
"""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import CurrentUser
from app.core.database import get_db
from app.core.permissions import require_roles
from app.core.patient_access import get_authorized_patient
from app.models.patient_code_status import PatientCodeStatus
from app.services.audit_logger import log_event

router = APIRouter(prefix="/patients/{patient_id}/code-status", tags=["code-status"])

from app.services.code_status_sync_service import (
    ALLOWED_CODE_STATUSES,
    set_current_code_status,
)


def _payload(row: PatientCodeStatus) -> dict:
    return {
        "code_status_id": str(row.id),
        "code_status": row.code_status,
        "effective_date": row.effective_date.isoformat() if row.effective_date else None,
        "source": row.source,
        "notes": row.notes,
        "is_current": row.is_current,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@router.get("", summary="Get current + historical code status for a patient")
def get_code_status(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["LVN", "RN", "NP", "MD", "MSW", "SC", "Surveyor"])),
):
    patient = get_authorized_patient(db, patient_id, user)

    tenant_id = getattr(patient, "tenant_id", None) or getattr(user, "tenant_id", None)

    rows = (
        db.query(PatientCodeStatus)
        .filter(
            PatientCodeStatus.patient_id == patient.id,
            PatientCodeStatus.tenant_id == tenant_id,
        )
        .order_by(PatientCodeStatus.effective_date.desc(), PatientCodeStatus.created_at.desc())
        .all()
    )

    current = next((row for row in rows if row.is_current), None)

    return {
        "current": _payload(current) if current else None,
        "history": [_payload(row) for row in rows],
    }


@router.post("", status_code=status.HTTP_201_CREATED, summary="Set a new current code status")
def set_code_status(
    *,
    patient_id: uuid.UUID,
    code_status: str,
    source: str = "FACESHEET",
    effective_date: date | None = None,
    notes: str | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["LVN", "RN", "NP", "MD"])),
):
    patient = get_authorized_patient(db, patient_id, user)

    code_status_clean = (code_status or "").strip().upper()
    if code_status_clean not in ALLOWED_CODE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"code_status must be one of {sorted(ALLOWED_CODE_STATUSES)}",
        )

    row = set_current_code_status(
        db,
        patient_id=patient.id,
        tenant_id=getattr(patient, "tenant_id", None) or getattr(user, "tenant_id", None),
        code_status=code_status_clean,
        source=(source or "FACESHEET").strip().upper(),
        effective_date=effective_date or date.today(),
        notes=(notes or "").strip() or None,
        updated_by=getattr(user, "id", None) or getattr(user, "user_id", None),
    )
    db.commit()
    db.refresh(row)

    log_event(
        user_id=user.user_id,
        role=user.role,
        action="SET_PATIENT_CODE_STATUS",
        entity_type="patient_code_status",
        entity_id=str(row.id),
    )

    return _payload(row)
