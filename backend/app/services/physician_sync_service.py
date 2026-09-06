# app/services/physician_sync_service.py

"""
Authoritative physician-role synchronization service.

Single source of truth: patient_physician_assignments
(PatientPhysicianAssignment). Facesheet, RNICA, CTI, Orders, and Care
Overview must all read from - and write through - this service so the
Attending Physician, Medical Director, Associate Medical Director, and
"will follow patient in hospice" designation can never disagree between
modules.

Unlike code status, this is a single shared *current* record per
(patient, role) rather than an append-only audit history - the ticket
only asks for one shared physician record consumed everywhere, not a
legal audit trail of physician changes over time.

This service does NOT commit. Caller owns the transaction boundary.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.patient_facesheet import PatientFaceSheet
from app.models.patient_physician_assignment import PatientPhysicianAssignment

ATTENDING = "ATTENDING"
MEDICAL_DIRECTOR = "MEDICAL_DIRECTOR"
ASSOCIATE_MEDICAL_DIRECTOR = "ASSOCIATE_MEDICAL_DIRECTOR"

ALLOWED_PHYSICIAN_ROLES = {ATTENDING, MEDICAL_DIRECTOR, ASSOCIATE_MEDICAL_DIRECTOR}

ALLOWED_PHYSICIAN_SOURCES = {
    "FACESHEET",
    "RNICA",
    "ADMISSION",
    "PHYSICIAN_DIRECTORY",
    "TENANT_DEFAULT",
    "OTHER",
}

_SOURCE_ALIASES = {
    "RN_ICA": "RNICA",
    "RN-ICA": "RNICA",
    "ADMISSION_WORKFLOW": "ADMISSION",
    "FACESHEET_MIGRATION": "FACESHEET",
    "DIRECTORY": "PHYSICIAN_DIRECTORY",
}

PHYSICIAN_ROLE_LABELS = {
    ATTENDING: "Attending Physician",
    MEDICAL_DIRECTOR: "Medical Director",
    ASSOCIATE_MEDICAL_DIRECTOR: "Associate Medical Director",
}

# Legacy PatientFaceSheet column prefixes mirrored for backward
# compatibility until every consumer reads the shared table.
_LEGACY_FIELD_PREFIX = {
    ATTENDING: "attending_physician",
    MEDICAL_DIRECTOR: "medical_director",
    ASSOCIATE_MEDICAL_DIRECTOR: "associate_medical_director",
}


def normalize_physician_role(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().upper().replace(" ", "_").replace("-", "_")
    if text in ALLOWED_PHYSICIAN_ROLES:
        return text
    return None


def normalize_physician_source(value: Any) -> str:
    text = str(value or "FACESHEET").strip().upper().replace(" ", "_").replace("-", "_")
    if not text:
        return "FACESHEET"
    if text in _SOURCE_ALIASES:
        return _SOURCE_ALIASES[text]
    if text in ALLOWED_PHYSICIAN_SOURCES:
        return text
    return "OTHER"


def get_physician_assignments(
    db: Session,
    *,
    patient_id,
    tenant_id=None,
) -> dict[str, PatientPhysicianAssignment]:
    """Return a dict keyed by role -> current PatientPhysicianAssignment row."""

    query = db.query(PatientPhysicianAssignment).filter(
        PatientPhysicianAssignment.patient_id == patient_id,
    )
    if tenant_id is not None:
        query = query.filter(PatientPhysicianAssignment.tenant_id == tenant_id)

    return {row.role: row for row in query.all()}


def set_physician_assignment(
    db: Session,
    *,
    patient_id,
    tenant_id,
    role: str,
    source: str,
    name: str | None = None,
    address: str | None = None,
    phone: str | None = None,
    fax: str | None = None,
    npi: str | None = None,
    will_follow_in_hospice: bool | None = None,
    physician_id=None,
    updated_by=None,
) -> PatientPhysicianAssignment | None:
    """
    Upsert the single shared record for (patient_id, role).

    A no-op (all fields None/unset) is ignored rather than clearing an
    existing assignment - callers should only pass the fields that
    changed.
    """

    normalized_role = normalize_physician_role(role)
    if normalized_role is None:
        raise ValueError(f"Unknown physician role: {role!r}")

    if tenant_id is None:
        raise ValueError("tenant_id is required")

    has_any_value = any(
        value is not None
        for value in (name, address, phone, fax, npi, will_follow_in_hospice, physician_id)
    )
    if not has_any_value:
        return None

    normalized_source = normalize_physician_source(source)
    now = datetime.now(timezone.utc)

    row = (
        db.query(PatientPhysicianAssignment)
        .filter(
            PatientPhysicianAssignment.patient_id == patient_id,
            PatientPhysicianAssignment.tenant_id == tenant_id,
            PatientPhysicianAssignment.role == normalized_role,
        )
        .first()
    )

    if row is None:
        row = PatientPhysicianAssignment(
            patient_id=patient_id,
            tenant_id=tenant_id,
            role=normalized_role,
            created_by=updated_by,
        )
        db.add(row)

    if name is not None:
        row.name = name
    if address is not None:
        row.address = address
    if phone is not None:
        row.phone = phone
    if fax is not None:
        row.fax = fax
    if npi is not None:
        row.npi = npi
    if will_follow_in_hospice is not None:
        row.will_follow_in_hospice = will_follow_in_hospice
    if physician_id is not None:
        row.physician_id = physician_id

    row.source = normalized_source
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
    row: PatientPhysicianAssignment,
    now: datetime,
    updated_by=None,
) -> None:
    """
    Keep the legacy PatientFaceSheet.<role>_* free-text columns as a
    display-only mirror for any legacy code still reading them directly.
    patient_physician_assignments remains the authoritative record.
    """

    facesheet = (
        db.query(PatientFaceSheet)
        .filter(PatientFaceSheet.patient_id == patient_id)
        .first()
    )
    if not facesheet:
        return

    prefix = _LEGACY_FIELD_PREFIX.get(role)
    if not prefix:
        return

    field_map = {
        f"{prefix}_name": row.name,
        f"{prefix}_address": row.address,
        f"{prefix}_phone": row.phone,
        f"{prefix}_fax": row.fax,
        f"{prefix}_npi": row.npi,
    }
    if role == ATTENDING:
        field_map[f"{prefix}_following"] = row.will_follow_in_hospice

    for field, value in field_map.items():
        if hasattr(facesheet, field) and value is not None:
            setattr(facesheet, field, value)

    if hasattr(facesheet, "updated_at"):
        facesheet.updated_at = now
    if updated_by and hasattr(facesheet, "updated_by"):
        facesheet.updated_by = updated_by


def apply_tenant_default_medical_director(
    db: Session,
    *,
    tenant_id,
    patient_id,
    updated_by=None,
) -> PatientPhysicianAssignment | None:
    """
    Prepopulate a NEW patient's Medical Director assignment from the
    tenant's configured default (Tenant.default_medical_director_physician_id).

    The hospice Medical Director is an agency governance decision, never
    something hospital documents determine -- this must never be called
    from document/HNP harvesting code paths.

    Precedence, per the multi-tenant design directive: an explicit
    per-patient assignment always wins over the tenant default, and the
    tenant default always wins over leaving the field blank. This function
    is therefore a strict no-op if:
      - a MEDICAL_DIRECTOR assignment already exists for this patient
        (someone already set one, explicitly or via an earlier call), or
      - the tenant has no default_medical_director_physician_id configured
        (shows as NOT_CONFIGURED in the UI -- never falls back to another
        tenant's physician, a dev seed, or SNS Hospice Solutions), or
      - the configured physician_id does not resolve to a physician in
        THIS tenant's own directory (belt-and-suspenders alongside the
        composite DB foreign key on tenants).
    """

    from app.models.physician import Physician
    from app.models.tenant import Tenant

    existing = get_physician_assignments(db, patient_id=patient_id, tenant_id=tenant_id)
    if MEDICAL_DIRECTOR in existing:
        return None

    tenant = db.get(Tenant, tenant_id)
    if tenant is None or not tenant.default_medical_director_physician_id:
        return None

    physician = (
        db.query(Physician)
        .filter(
            Physician.id == tenant.default_medical_director_physician_id,
            Physician.tenant_id == tenant_id,
        )
        .first()
    )
    if physician is None:
        return None

    display_name = physician.display_name or " ".join(
        part for part in (physician.first_name, physician.last_name) if part
    ).strip()
    if not display_name:
        return None

    return set_physician_assignment(
        db,
        patient_id=patient_id,
        tenant_id=tenant_id,
        role=MEDICAL_DIRECTOR,
        source="TENANT_DEFAULT",
        name=display_name,
        address=", ".join(
            part
            for part in (
                physician.address_street,
                physician.address_city,
                physician.address_state,
                physician.address_zip,
            )
            if part
        )
        or None,
        phone=physician.phone,
        fax=physician.fax,
        npi=physician.npi,
        physician_id=physician.id,
        updated_by=updated_by,
    )
