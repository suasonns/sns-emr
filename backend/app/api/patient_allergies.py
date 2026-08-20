# app/api/patient_allergies.py

"""
Structured patient allergy management.

Feeds the medication safety engine (app/services/drug_safety_service.py) so
new/active medications can be cross-checked against a patient's documented
allergies in real time.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import CurrentUser
from app.core.database import get_db
from app.core.permissions import require_roles
from app.core.patient_access import get_authorized_patient
from app.models.patient import Patient
from app.models.patient_allergy import PatientAllergy
from app.services.audit_logger import log_event
from app.services.drug_safety_service import resolve_allergen

router = APIRouter(prefix="/patients/{patient_id}/allergies", tags=["allergies"])

_ALLOWED_TYPES = {"DRUG", "FOOD", "ENVIRONMENTAL", "OTHER"}
_ALLOWED_SEVERITIES = {"MILD", "MODERATE", "SEVERE", "ANAPHYLAXIS"}


@router.get("", summary="List a patient's allergies")
def list_allergies(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["LVN", "RN", "NP", "MD", "MSW", "SC", "Surveyor"])),
):
    patient = get_authorized_patient(db, patient_id, user)

    rows = (
        db.query(PatientAllergy)
        .filter(PatientAllergy.patient_id == patient.id, PatientAllergy.active.is_(True))
        .order_by(PatientAllergy.created_at.desc())
        .all()
    )

    return [
        {
            "allergy_id": str(a.id),
            "allergen_text": a.allergen_text,
            "allergen_type": a.allergen_type,
            "drug_class": a.drug_class,
            "reaction_description": a.reaction_description,
            "severity": a.severity,
        }
        for a in rows
    ]


@router.post("", status_code=status.HTTP_201_CREATED, summary="Add a patient allergy")
def add_allergy(
    *,
    patient_id: uuid.UUID,
    allergen_text: str,
    allergen_type: str = "DRUG",
    reaction_description: str | None = None,
    severity: str | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["LVN", "RN", "NP", "MD", "MSW", "SC"])),
):
    patient = get_authorized_patient(db, patient_id, user)

    allergen_clean = (allergen_text or "").strip()
    if not allergen_clean:
        raise HTTPException(status_code=400, detail="allergen_text is required")

    allergen_type_clean = (allergen_type or "DRUG").strip().upper()
    if allergen_type_clean not in _ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"allergen_type must be one of {sorted(_ALLOWED_TYPES)}")

    severity_clean = (severity or "").strip().upper() or None
    if severity_clean and severity_clean not in _ALLOWED_SEVERITIES:
        raise HTTPException(status_code=400, detail=f"severity must be one of {sorted(_ALLOWED_SEVERITIES)}")

    drug_class = None
    if allergen_type_clean == "DRUG":
        drug_class, _ = resolve_allergen(allergen_clean)

    allergy = PatientAllergy(
        patient_id=patient.id,
        allergen_text=allergen_clean,
        allergen_type=allergen_type_clean,
        drug_class=drug_class,
        reaction_description=(reaction_description or "").strip() or None,
        severity=severity_clean,
        active=True,
    )

    db.add(allergy)
    db.commit()
    db.refresh(allergy)

    log_event(
        user_id=user.user_id,
        role=user.role,
        action="ADD_PATIENT_ALLERGY",
        entity_type="patient_allergy",
        entity_id=str(allergy.id),
    )

    return {
        "allergy_id": str(allergy.id),
        "allergen_text": allergy.allergen_text,
        "allergen_type": allergy.allergen_type,
        "drug_class": allergy.drug_class,
        "severity": allergy.severity,
    }


@router.delete("/{allergy_id}", summary="Remove (deactivate) a patient allergy")
def remove_allergy(
    patient_id: uuid.UUID,
    allergy_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["RN", "NP", "MD"])),
):
    get_authorized_patient(db, patient_id, user)
    allergy = (
        db.query(PatientAllergy)
        .filter(PatientAllergy.id == allergy_id, PatientAllergy.patient_id == patient_id)
        .first()
    )
    if not allergy:
        raise HTTPException(status_code=404, detail="Allergy record not found")

    allergy.active = False
    db.commit()

    log_event(
        user_id=user.user_id,
        role=user.role,
        action="REMOVE_PATIENT_ALLERGY",
        entity_type="patient_allergy",
        entity_id=str(allergy.id),
    )

    return {"allergy_id": str(allergy.id), "status": "inactive"}
