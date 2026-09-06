# app/api/patient_contacts.py

"""
Structured caregiver/decision-maker management (Primary Caregiver,
Responsible Party, DPOA, Healthcare Agent, Decision Maker, Guardian,
Conservator, Emergency Contact).

Authoritative record consumed by Facesheet, RNICA, ACP, and Consents so
these roles can never disagree between modules. Document-harvested
values that conflict with an existing entry are queued as
PatientContactSuggestion rows (see contact_harvest_service) and surfaced/
resolved through the suggestion endpoints below rather than silently
applied.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import CurrentUser
from app.core.database import get_db
from app.core.permissions import require_roles
from app.core.patient_access import get_authorized_patient
from app.models.patient_contact import PatientContact
from app.models.patient_contact_suggestion import PatientContactSuggestion
from app.services.audit_logger import log_event
from app.services.contact_sync_service import (
    ALLOWED_CONTACT_ROLES,
    CONTACT_ROLE_LABELS,
    get_patient_contacts,
    set_patient_contact,
)

router = APIRouter(prefix="/patients/{patient_id}/contacts", tags=["contacts"])


def _payload(row: PatientContact) -> dict:
    return {
        "role": row.role,
        "role_label": CONTACT_ROLE_LABELS.get(row.role, row.role),
        "name": row.name,
        "relationship": row.relationship_to_patient,
        "phone": row.phone,
        "email": row.email,
        "address": row.address,
        "is_preferred": bool(row.is_preferred),
        "source": row.source,
        "attribution_source": row.attribution_source,
        "source_document_id": str(row.source_document_id) if row.source_document_id else None,
        "source_document_name": row.source_document_name,
        "extractor_version": row.extractor_version,
        "extraction_timestamp": row.extraction_timestamp.isoformat() if row.extraction_timestamp else None,
        "manual_override": bool(row.manual_override),
        "manual_override_by": str(row.manual_override_by) if row.manual_override_by else None,
        "manual_override_at": row.manual_override_at.isoformat() if row.manual_override_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _suggestion_payload(row: PatientContactSuggestion) -> dict:
    return {
        "id": str(row.id),
        "role": row.role,
        "role_label": CONTACT_ROLE_LABELS.get(row.role, row.role),
        "field_name": row.field_name,
        "current_value": row.current_value,
        "suggested_value": row.suggested_value,
        "source_document_id": str(row.source_document_id) if row.source_document_id else None,
        "source_document_name": row.source_document_name,
        "extractor_version": row.extractor_version,
        "extraction_timestamp": row.extraction_timestamp.isoformat() if row.extraction_timestamp else None,
        "status": row.status,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "resolved_at": row.resolved_at.isoformat() if row.resolved_at else None,
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
    email: str | None = None,
    address: str | None = None,
    is_preferred: bool | None = None,
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
        email=email,
        address=address,
        is_preferred=is_preferred,
        updated_by=getattr(user, "id", None) or getattr(user, "user_id", None),
        # A human explicitly submitted this via the manual contact-entry
        # endpoint -- stamp manual_override so any later conflicting
        # document-harvested value is always queued for review rather
        # than silently reapplied.
        is_manual_entry=True,
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


@router.get(
    "/suggestions",
    summary="List document-harvested contact suggestions pending review",
)
def list_contact_suggestions(
    patient_id: uuid.UUID,
    status_filter: str = "pending",
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["LVN", "RN", "NP", "MD", "MSW", "SC", "Surveyor"])),
):
    patient = get_authorized_patient(db, patient_id, user)
    tenant_id = getattr(patient, "tenant_id", None) or getattr(user, "tenant_id", None)

    query = db.query(PatientContactSuggestion).filter(
        PatientContactSuggestion.patient_id == patient.id,
        PatientContactSuggestion.tenant_id == tenant_id,
    )
    if status_filter and status_filter != "all":
        query = query.filter(PatientContactSuggestion.status == status_filter)

    rows = query.order_by(PatientContactSuggestion.created_at.desc()).all()
    return [_suggestion_payload(row) for row in rows]


def _resolve_suggestion(
    db: Session,
    *,
    patient_id: uuid.UUID,
    suggestion_id: uuid.UUID,
    user: CurrentUser,
    tenant_id,
) -> PatientContactSuggestion:
    suggestion = (
        db.query(PatientContactSuggestion)
        .filter(
            PatientContactSuggestion.id == suggestion_id,
            PatientContactSuggestion.patient_id == patient_id,
            PatientContactSuggestion.tenant_id == tenant_id,
        )
        .first()
    )
    if suggestion is None:
        raise HTTPException(status_code=404, detail="Contact suggestion not found")
    if suggestion.status != "pending":
        raise HTTPException(status_code=409, detail=f"Suggestion already {suggestion.status}")
    return suggestion


@router.post(
    "/suggestions/{suggestion_id}/accept",
    summary="Accept a harvested contact suggestion and apply it",
)
def accept_contact_suggestion(
    *,
    patient_id: uuid.UUID,
    suggestion_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["LVN", "RN", "NP", "MD", "MSW", "SC"])),
):
    patient = get_authorized_patient(db, patient_id, user)
    tenant_id = getattr(patient, "tenant_id", None) or getattr(user, "tenant_id", None)

    suggestion = _resolve_suggestion(
        db, patient_id=patient.id, suggestion_id=suggestion_id, user=user, tenant_id=tenant_id
    )

    updated_by = getattr(user, "id", None) or getattr(user, "user_id", None)
    row = set_patient_contact(
        db,
        patient_id=patient.id,
        tenant_id=tenant_id,
        role=suggestion.role,
        source="DOCUMENT_HARVEST",
        attribution_source="HARVESTED",
        source_document_id=suggestion.source_document_id,
        source_document_name=suggestion.source_document_name,
        extractor_version=suggestion.extractor_version,
        extraction_timestamp=suggestion.extraction_timestamp,
        updated_by=updated_by,
        **{suggestion.field_name: suggestion.suggested_value},
    )

    now = datetime.now(timezone.utc)
    suggestion.status = "accepted"
    suggestion.resolved_at = now
    suggestion.resolved_by = updated_by
    db.commit()

    log_event(
        user_id=user.user_id,
        role=user.role,
        action="ACCEPT_PATIENT_CONTACT_SUGGESTION",
        entity_type="patient_contact_suggestion",
        entity_id=str(suggestion.id),
    )

    return {"suggestion": _suggestion_payload(suggestion), "contact": _payload(row) if row else None}


@router.post(
    "/suggestions/{suggestion_id}/reject",
    summary="Reject a harvested contact suggestion",
)
def reject_contact_suggestion(
    *,
    patient_id: uuid.UUID,
    suggestion_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["LVN", "RN", "NP", "MD", "MSW", "SC"])),
):
    patient = get_authorized_patient(db, patient_id, user)
    tenant_id = getattr(patient, "tenant_id", None) or getattr(user, "tenant_id", None)

    suggestion = _resolve_suggestion(
        db, patient_id=patient.id, suggestion_id=suggestion_id, user=user, tenant_id=tenant_id
    )

    updated_by = getattr(user, "id", None) or getattr(user, "user_id", None)
    suggestion.status = "rejected"
    suggestion.resolved_at = datetime.now(timezone.utc)
    suggestion.resolved_by = updated_by
    db.commit()

    log_event(
        user_id=user.user_id,
        role=user.role,
        action="REJECT_PATIENT_CONTACT_SUGGESTION",
        entity_type="patient_contact_suggestion",
        entity_id=str(suggestion.id),
    )

    return _suggestion_payload(suggestion)


@router.post(
    "/suggestions/{suggestion_id}/dismiss",
    summary="Dismiss a harvested contact suggestion without applying or rejecting it",
)
def dismiss_contact_suggestion(
    *,
    patient_id: uuid.UUID,
    suggestion_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["LVN", "RN", "NP", "MD", "MSW", "SC"])),
):
    patient = get_authorized_patient(db, patient_id, user)
    tenant_id = getattr(patient, "tenant_id", None) or getattr(user, "tenant_id", None)

    suggestion = _resolve_suggestion(
        db, patient_id=patient.id, suggestion_id=suggestion_id, user=user, tenant_id=tenant_id
    )

    updated_by = getattr(user, "id", None) or getattr(user, "user_id", None)
    suggestion.status = "dismissed"
    suggestion.resolved_at = datetime.now(timezone.utc)
    suggestion.resolved_by = updated_by
    db.commit()

    log_event(
        user_id=user.user_id,
        role=user.role,
        action="DISMISS_PATIENT_CONTACT_SUGGESTION",
        entity_type="patient_contact_suggestion",
        entity_id=str(suggestion.id),
    )

    return _suggestion_payload(suggestion)

