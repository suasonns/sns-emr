# app/services/code_status_sync_service.py

"""
Authoritative code-status synchronization service.

Single source of truth: patient_code_statuses (PatientCodeStatus).
Facesheet, RNICA, ACP/consent, Care Overview, and Orders must all read
from - and write through - this service so a Full Code / DNR / DNI /
DNR-DNI / Comfort Measures Only designation can never disagree between
modules.

This service does NOT commit. Caller owns the transaction boundary.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.patient_code_status import PatientCodeStatus
from app.models.patient_facesheet import PatientFaceSheet

ALLOWED_CODE_STATUSES = {"FULL_CODE", "DNR_DNI", "COMFORT_MEASURES_ONLY", "OTHER"}

# Ticket-specified source values. Any source not in this set is normalized
# to OTHER (never rejected outright) so a save never fails because of an
# unrecognized workflow name, but the stored value always stays validated.
ALLOWED_CODE_STATUS_SOURCES = {
    "FACESHEET",
    "RNICA",
    "POLST",
    "ADVANCE_DIRECTIVE",
    "PHYSICIAN_ORDER",
    "HOSPITAL_RECORD",
    "PATIENT_REPRESENTATIVE",
    "OTHER",
}

_SOURCE_ALIASES = {
    "RN_ICA": "RNICA",
    "RN-ICA": "RNICA",
    "ADVANCED_CARE_PLANNING": "ADVANCE_DIRECTIVE",
    "ACP": "ADVANCE_DIRECTIVE",
    "PHYSICIAN": "PHYSICIAN_ORDER",
    "MD_ORDER": "PHYSICIAN_ORDER",
    "HOSPITAL": "HOSPITAL_RECORD",
    "PATIENT_REP": "PATIENT_REPRESENTATIVE",
    "FAMILY": "PATIENT_REPRESENTATIVE",
    "FACESHEET_MIGRATION": "FACESHEET",
}

# Legacy free-text label mirror kept on PatientFaceSheet.code_status for
# backward compatibility until every consumer reads the shared table.
CODE_STATUS_DISPLAY_LABELS = {
    "FULL_CODE": "Full Code",
    "DNR_DNI": "DNR/DNI",
    "COMFORT_MEASURES_ONLY": "Comfort Measures Only",
    "OTHER": "Other",
}
_DISPLAY_LABELS = CODE_STATUS_DISPLAY_LABELS


def normalize_code_status_source(value: Any) -> str:
    """
    Validate/normalize a code-status source against the ticket's allowed
    list. Never raises - an unrecognized source is preserved for the
    migration case (FACESHEET_MIGRATION stays mapped to FACESHEET) or
    else normalized to OTHER, so a bad/unknown source label never blocks
    a clinically urgent code-status save.
    """

    text = str(value or "FACESHEET").strip().upper().replace(" ", "_").replace("-", "_")

    if not text:
        return "FACESHEET"

    if text in _SOURCE_ALIASES:
        return _SOURCE_ALIASES[text]

    if text in ALLOWED_CODE_STATUS_SOURCES:
        return text

    return "OTHER"


def normalize_code_status(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip().upper().replace(" ", "_").replace("-", "_")

    if not text:
        return None

    aliases = {
        "FULL_CODE": "FULL_CODE",
        "FULLCODE": "FULL_CODE",
        "FULL": "FULL_CODE",
        "DNR": "DNR_DNI",
        "DNI": "DNR_DNI",
        "DNR/DNI": "DNR_DNI",
        "DNR_DNI": "DNR_DNI",
        "DNRDNI": "DNR_DNI",
        "COMFORT_MEASURES_ONLY": "COMFORT_MEASURES_ONLY",
        "COMFORT_MEASURES": "COMFORT_MEASURES_ONLY",
        "CMO": "COMFORT_MEASURES_ONLY",
    }

    if text in aliases:
        return aliases[text]

    if text in ALLOWED_CODE_STATUSES:
        return text

    return "OTHER"


def get_current_code_status(
    db: Session,
    *,
    patient_id,
    tenant_id=None,
) -> PatientCodeStatus | None:
    query = db.query(PatientCodeStatus).filter(
        PatientCodeStatus.patient_id == patient_id,
        PatientCodeStatus.is_current.is_(True),
    )
    if tenant_id is not None:
        query = query.filter(PatientCodeStatus.tenant_id == tenant_id)
    return query.order_by(PatientCodeStatus.created_at.desc()).first()


def set_current_code_status(
    db: Session,
    *,
    patient_id,
    tenant_id,
    code_status: str,
    source: str,
    effective_date: date | None = None,
    notes: str | None = None,
    updated_by=None,
) -> PatientCodeStatus:
    """
    Record a new current code status.

    If the incoming value matches the existing current row's code_status
    (same value, ignoring source/notes), the existing row is returned
    unchanged rather than creating a redundant duplicate entry - but any
    genuine change (including a same-value re-affirmation from a
    different source, e.g. a POLST confirming what intake already said)
    always creates a new historical row so the audit trail is complete.
    """

    normalized = normalize_code_status(code_status)
    if normalized is None:
        raise ValueError("code_status is required")

    if tenant_id is None:
        raise ValueError("tenant_id is required")

    normalized_source = normalize_code_status_source(source)

    now = datetime.now(timezone.utc)
    current = get_current_code_status(db, patient_id=patient_id, tenant_id=tenant_id)

    if (
        current is not None
        and current.code_status == normalized
        and current.source == normalized_source
    ):
        # Same value from the same source - avoid a no-op duplicate row.
        return current

    if current is not None:
        current.is_current = False
        current.updated_at = now
        db.flush()

    new_row = PatientCodeStatus(
        patient_id=patient_id,
        tenant_id=tenant_id,
        code_status=normalized,
        effective_date=effective_date or date.today(),
        source=normalized_source,
        notes=notes,
        is_current=True,
        created_by=updated_by,
    )
    db.add(new_row)
    db.flush()

    _mirror_to_legacy_facesheet_field(
        db,
        patient_id=patient_id,
        code_status=normalized,
        now=now,
        updated_by=updated_by,
    )

    return new_row


def _mirror_to_legacy_facesheet_field(
    db: Session,
    *,
    patient_id,
    code_status: str,
    now: datetime,
    updated_by=None,
) -> None:
    """
    Keep PatientFaceSheet.code_status as a display-only mirror for any
    legacy code still reading it directly. patient_code_statuses remains
    the authoritative record.
    """

    facesheet = (
        db.query(PatientFaceSheet)
        .filter(PatientFaceSheet.patient_id == patient_id)
        .first()
    )

    if not facesheet:
        return

    facesheet.code_status = _DISPLAY_LABELS.get(code_status, code_status)

    if hasattr(facesheet, "updated_at"):
        facesheet.updated_at = now

    if updated_by and hasattr(facesheet, "updated_by"):
        facesheet.updated_by = updated_by
