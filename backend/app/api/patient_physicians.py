# app/api/patient_physicians.py

"""
Structured physician-role management (Attending, Medical Director,
Associate Medical Director).

Authoritative record consumed by Facesheet, RNICA, CTI, Orders, and Care
Overview so the physician assigned to each role can never disagree
between modules.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import CurrentUser
from app.core.database import get_db
from app.core.permissions import require_roles
from app.core.patient_access import get_authorized_patient
from app.models.patient_physician_assignment import PatientPhysicianAssignment
from app.services.audit_logger import log_event
from app.services.physician_sync_service import (
    ALLOWED_PHYSICIAN_ROLES,
    get_physician_assignments,
    set_physician_assignment,
)

router = APIRouter(prefix="/patients/{patient_id}/physicians", tags=["physicians"])


def _payload(row: PatientPhysicianAssignment) -> dict:
    return {
        "role": row.role,
        "name": row.name,
        "address": row.address,
        "phone": row.phone,
        "fax": row.fax,
        "npi": row.npi,
        "will_follow_in_hospice": row.will_follow_in_hospice,
        "source": row.source,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@router.get("", summary="Get all shared physician-role assignments for a patient")
def get_physicians(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["LVN", "RN", "NP", "MD", "MSW", "SC", "Surveyor"])),
):
    patient = get_authorized_patient(db, patient_id, user)
    tenant_id = getattr(patient, "tenant_id", None) or getattr(user, "tenant_id", None)

    assignments = get_physician_assignments(db, patient_id=patient.id, tenant_id=tenant_id)

    return {
        "attending": _payload(assignments["ATTENDING"]) if "ATTENDING" in assignments else None,
        "medical_director": _payload(assignments["MEDICAL_DIRECTOR"]) if "MEDICAL_DIRECTOR" in assignments else None,
        "associate_medical_director": (
            _payload(assignments["ASSOCIATE_MEDICAL_DIRECTOR"])
            if "ASSOCIATE_MEDICAL_DIRECTOR" in assignments
            else None
        ),
    }


@router.post("", status_code=status.HTTP_200_OK, summary="Set the shared physician for a role")
def set_physician(
    *,
    patient_id: uuid.UUID,
    role: str,
    source: str = "FACESHEET",
    name: str | None = None,
    address: str | None = None,
    phone: str | None = None,
    fax: str | None = None,
    npi: str | None = None,
    will_follow_in_hospice: bool | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["LVN", "RN", "NP", "MD"])),
):
    patient = get_authorized_patient(db, patient_id, user)

    role_clean = (role or "").strip().upper()
    if role_clean not in ALLOWED_PHYSICIAN_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"role must be one of {sorted(ALLOWED_PHYSICIAN_ROLES)}",
        )

    row = set_physician_assignment(
        db,
        patient_id=patient.id,
        tenant_id=getattr(patient, "tenant_id", None) or getattr(user, "tenant_id", None),
        role=role_clean,
        source=source,
        name=name,
        address=address,
        phone=phone,
        fax=fax,
        npi=npi,
        will_follow_in_hospice=will_follow_in_hospice,
        updated_by=getattr(user, "id", None) or getattr(user, "user_id", None),
    )

    if row is None:
        raise HTTPException(status_code=400, detail="At least one physician field must be provided")

    db.commit()
    db.refresh(row)

    log_event(
        user_id=user.user_id,
        role=user.role,
        action="SET_PATIENT_PHYSICIAN_ASSIGNMENT",
        entity_type="patient_physician_assignment",
        entity_id=str(row.id),
    )

    return _payload(row)
