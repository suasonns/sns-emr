# app/api/patient_contacts.py

"""
Structured caregiver/decision-maker management (Primary Caregiver,
Responsible Party, DPOA, Healthcare Agent, Decision Maker, Emergency
Contact).

Authoritative record consumed by Facesheet, RNICA, ACP, and Consents so
these roles can never disagree between modules.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import CurrentUser
from app.core.database import get_db
from app.core.permissions import require_roles
from app.core.patient_access import get_authorized_patient
from app.models.patient_contact import PatientContact
from app.services.audit_logger import log_event
from app.services.contact_sync_service import (
    ALLOWED_CONTACT_ROLES,
    get_patient_contacts,
    set_patient_contact,
)

router = APIRouter(prefix="/patients/{patient_id}/contacts", tags=["contacts"])


def _payload(row: PatientContact) -> dict:
    return {
        "role": row.role,
        "name": row.name,
        "relationship": row.relationship_to_patient,
        "phone": row.phone,
        "address": row.address,
        "source": row.source,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@router.get("", summary="Get all shared caregiver/decision-maker contacts for a patient")
def get_contacts(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["LVN", "RN", "NP", "MD", "MSW", "SC", "Surveyor"])),
):
    patient = get_authorized_patient(db, patient_id, user)
    tenant_id = getattr(patient, "tenant_id", None) or getattr(user, "tenant_id", None)

    contacts = get_patient_contacts(db, patient_id=patient.id, tenant_id=tenant_id)

    return {role.lower(): _payload(row) for role, row in contacts.items()}


@router.post("", status_code=status.HTTP_200_OK, summary="Set the shared contact for a role")
def set_contact(
    *,
    patient_id: uuid.UUID,
    role: str,
    source: str = "FACESHEET",
    name: str | None = None,
    relationship: str | None = None,
    phone: str | None = None,
    address: str | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["LVN", "RN", "NP", "MD", "MSW", "SC"])),
):
    patient = get_authorized_patient(db, patient_id, user)

    role_clean = (role or "").strip().upper()
    if role_clean not in ALLOWED_CONTACT_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"role must be one of {sorted(ALLOWED_CONTACT_ROLES)}",
        )

    row = set_patient_contact(
        db,
        patient_id=patient.id,
        tenant_id=getattr(patient, "tenant_id", None) or getattr(user, "tenant_id", None),
        role=role_clean,
        source=source,
        name=name,
        relationship_to_patient=relationship,
        phone=phone,
        address=address,
        updated_by=getattr(user, "id", None) or getattr(user, "user_id", None),
    )

    if row is None:
        raise HTTPException(status_code=400, detail="At least one contact field must be provided")

    db.commit()
    db.refresh(row)

    log_event(
        user_id=user.user_id,
        role=user.role,
        action="SET_PATIENT_CONTACT",
        entity_type="patient_contact",
        entity_id=str(row.id),
    )

    return _payload(row)
