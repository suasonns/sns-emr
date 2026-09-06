# app/services/contact_sync_service.py

"""
Authoritative caregiver/decision-maker synchronization service.

Single source of truth: patient_contacts (PatientContact). Facesheet,
RNICA, ACP, and Consents must all read from - and write through - this
service so Primary Caregiver, Responsible Party, DPOA, Healthcare Agent,
Decision Maker, and Emergency Contact can never disagree between
modules.

Like physician assignments, this is a single shared *current* record per
(patient, role) rather than an append-only audit history.

This service does NOT commit. Caller owns the transaction boundary.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.patient_contact import PatientContact
from app.models.patient_facesheet import PatientFaceSheet

PRIMARY_CAREGIVER = "PRIMARY_CAREGIVER"
RESPONSIBLE_PARTY = "RESPONSIBLE_PARTY"
DPOA = "DPOA"
HEALTHCARE_AGENT = "HEALTHCARE_AGENT"
DECISION_MAKER = "DECISION_MAKER"
EMERGENCY_CONTACT = "EMERGENCY_CONTACT"
GUARDIAN = "GUARDIAN"
CONSERVATOR = "CONSERVATOR"

ALLOWED_CONTACT_ROLES = {
    PRIMARY_CAREGIVER,
    RESPONSIBLE_PARTY,
    DPOA,
    HEALTHCARE_AGENT,
    DECISION_MAKER,
    EMERGENCY_CONTACT,
    GUARDIAN,
    CONSERVATOR,
}

ALLOWED_CONTACT_SOURCES = {
    "FACESHEET",
    "RNICA",
    "ACP",
    "CONSENT",
    "OTHER",
    "DOCUMENT_HARVEST",
}

_SOURCE_ALIASES = {
    "RN_ICA": "RNICA",
    "RN-ICA": "RNICA",
    "ADVANCE_DIRECTIVE": "ACP",
    "ADVANCED_CARE_PLANNING": "ACP",
    "CONSENTS": "CONSENT",
    "FACESHEET_MIGRATION": "FACESHEET",
    "DOCUMENT_UPLOAD": "DOCUMENT_HARVEST",
    "HARVEST": "DOCUMENT_HARVEST",
}

CONTACT_ROLE_LABELS = {
    PRIMARY_CAREGIVER: "Primary Caregiver",
    RESPONSIBLE_PARTY: "Responsible Party",
    DPOA: "Durable Power of Attorney",
    HEALTHCARE_AGENT: "Healthcare Agent",
    DECISION_MAKER: "Decision Maker",
    EMERGENCY_CONTACT: "Emergency Contact",
    GUARDIAN: "Guardian",
    CONSERVATOR: "Conservator",
}

# HOW the current value arrived, distinct from `source` (WHICH module).
ATTRIBUTION_HARVESTED = "HARVESTED"
ATTRIBUTION_MANUAL = "MANUAL"
ATTRIBUTION_CALCULATED = "CALCULATED"
ATTRIBUTION_IMPORTED = "IMPORTED"

ALLOWED_ATTRIBUTION_SOURCES = {
    ATTRIBUTION_HARVESTED,
    ATTRIBUTION_MANUAL,
    ATTRIBUTION_CALCULATED,
    ATTRIBUTION_IMPORTED,
}

# Legacy PatientFaceSheet column prefixes mirrored for backward
# compatibility until every consumer reads the shared table.
_LEGACY_FIELD_PREFIX = {
    RESPONSIBLE_PARTY: "responsible_party",
    EMERGENCY_CONTACT: "emergency_contact",
}


def normalize_contact_role(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().upper().replace(" ", "_").replace("-", "_")
    if text in ALLOWED_CONTACT_ROLES:
        return text
    return None


def normalize_contact_source(value: Any) -> str:
    text = str(value or "FACESHEET").strip().upper().replace(" ", "_").replace("-", "_")
    if not text:
        return "FACESHEET"
    if text in _SOURCE_ALIASES:
        return _SOURCE_ALIASES[text]
    if text in ALLOWED_CONTACT_SOURCES:
        return text
    return "OTHER"


def get_patient_contacts(
    db: Session,
    *,
    patient_id,
    tenant_id=None,
) -> dict[str, PatientContact]:
    """Return a dict keyed by role -> current PatientContact row."""

    query = db.query(PatientContact).filter(PatientContact.patient_id == patient_id)
    if tenant_id is not None:
        query = query.filter(PatientContact.tenant_id == tenant_id)

    return {row.role: row for row in query.all()}


def set_patient_contact(
    db: Session,
    *,
    patient_id,
    tenant_id,
    role: str,
    source: str,
    name: str | None = None,
    relationship_to_patient: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    address: str | None = None,
    is_preferred: bool | None = None,
    updated_by=None,
    attribution_source: str | None = None,
    source_document_id=None,
    source_document_name: str | None = None,
    source_document_page: int | None = None,
    extractor_version: str | None = None,
    extraction_timestamp: datetime | None = None,
    is_manual_entry: bool = False,
) -> PatientContact | None:
    """
    Upsert the single shared record for (patient_id, role).

    A no-op (all fields None/unset) is ignored rather than clearing an
    existing contact - callers should only pass the fields that changed.

    `is_manual_entry=True` (used by the human-facing contact-entry
    endpoint) stamps manual_override/manual_override_by/
    manual_override_at so that any LATER conflicting document-harvested
    value is always queued for review instead of silently applied - see
    app.services.contact_harvest_service. This function itself never
    resolves a conflict; callers responsible for harvesting (rather than
    direct human entry) must check for an existing, differing value
    themselves before calling this.
    """

    normalized_role = normalize_contact_role(role)
    if normalized_role is None:
        raise ValueError(f"Unknown contact role: {role!r}")

    if tenant_id is None:
        raise ValueError("tenant_id is required")

    has_any_value = any(
        value is not None
        for value in (name, relationship_to_patient, phone, email, address, is_preferred)
    )
    if not has_any_value:
        return None

    normalized_source = normalize_contact_source(source)
    now = datetime.now(timezone.utc)

    row = (
        db.query(PatientContact)
        .filter(
            PatientContact.patient_id == patient_id,
            PatientContact.tenant_id == tenant_id,
            PatientContact.role == normalized_role,
        )
        .first()
    )

    if row is None:
        row = PatientContact(
            patient_id=patient_id,
            tenant_id=tenant_id,
            role=normalized_role,
            created_by=updated_by,
        )
        db.add(row)

    if name is not None:
        row.name = name
    if relationship_to_patient is not None:
        row.relationship_to_patient = relationship_to_patient
    if phone is not None:
        row.phone = phone
    if email is not None:
        row.email = email
    if is_preferred is not None:
        row.is_preferred = is_preferred
    if address is not None:
        row.address = address

    row.source = normalized_source

    if attribution_source is not None:
        normalized_attribution = str(attribution_source).strip().upper()
        row.attribution_source = (
            normalized_attribution
            if normalized_attribution in ALLOWED_ATTRIBUTION_SOURCES
            else ATTRIBUTION_MANUAL
        )
    elif is_manual_entry:
        row.attribution_source = ATTRIBUTION_MANUAL

    if source_document_id is not None:
        row.source_document_id = source_document_id
    if source_document_name is not None:
        row.source_document_name = source_document_name
    if source_document_page is not None:
        row.source_document_page = source_document_page
    if extractor_version is not None:
        row.extractor_version = extractor_version
    if extraction_timestamp is not None:
        row.extraction_timestamp = extraction_timestamp

    if is_manual_entry:
        row.manual_override = True
        row.manual_override_by = updated_by
        row.manual_override_at = now

    row.updated_by = updated_by
    row.updated_at = now
    db.flush()

    _mirror_to_legacy_facesheet_fields(
        db,
        patient_id=patient_id,
        role=normalized_role,
        row=row,
        now=now,
        updated_by=updated_by,
    )

    return row


def _mirror_to_legacy_facesheet_fields(
    db: Session,
    *,
    patient_id,
    role: str,
    row: PatientContact,
    now: datetime,
    updated_by=None,
) -> None:
    """
    Keep the legacy PatientFaceSheet.<role>_* free-text columns as a
    display-only mirror for any legacy code still reading them directly.
    patient_contacts remains the authoritative record. Only
    RESPONSIBLE_PARTY and EMERGENCY_CONTACT have legacy Facesheet columns
    - PRIMARY_CAREGIVER/DPOA/HEALTHCARE_AGENT/DECISION_MAKER are new
    roles with no legacy facesheet mirror to maintain.
    """

    prefix = _LEGACY_FIELD_PREFIX.get(role)
    if not prefix:
        return

    facesheet = (
        db.query(PatientFaceSheet)
        .filter(PatientFaceSheet.patient_id == patient_id)
        .first()
    )
    if not facesheet:
        return

    field_map = {
        f"{prefix}_name": row.name,
        f"{prefix}_relationship": row.relationship_to_patient,
        f"{prefix}_phone": row.phone,
    }

    for field, value in field_map.items():
        if hasattr(facesheet, field) and value is not None:
            setattr(facesheet, field, value)

    if hasattr(facesheet, "updated_at"):
        facesheet.updated_at = now
    if updated_by and hasattr(facesheet, "updated_by"):
        facesheet.updated_by = updated_by
