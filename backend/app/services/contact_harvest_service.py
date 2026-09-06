# app/services/contact_harvest_service.py

"""
Document-driven harvesting for shared caregiver/decision-maker contacts
(PatientContact): Emergency Contact, Responsible Party, Healthcare Agent,
DPOA, Guardian, Conservator, Primary Caregiver, Decision Maker.

Mirrors the reconciliation discipline already proven for demographic
facesheet fields (see app.api.patients._reconcile_demographic_field /
FacesheetFieldSuggestion) and diagnosis provenance (PatientDiagnosis.
source_document_id): an AI-extracted key finding is applied directly only
when the target field is currently empty. Any conflicting, already-
populated value is NEVER silently overwritten -- it is queued as a
PatientContactSuggestion for a human to accept/reject/dismiss via the
patient contact-suggestions endpoints. This is the single harvesting
entry point for contacts; callers (document_harvest_job) must not
duplicate this parsing/reconciliation logic inline.

Read-only with respect to source text: this module never fabricates a
name, phone, email, or address that is not present in the document's
AI-extracted key findings.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.document_record import DocumentRecord
from app.models.patient_contact_suggestion import PatientContactSuggestion
from app.services.contact_sync_service import (
    ATTRIBUTION_HARVESTED,
    get_patient_contacts,
    set_patient_contact,
)

# Bumped whenever the label/value parsing heuristics below change in a way
# that could alter previously-harvested output -- lets a future audit tell
# which extractor version produced a given PatientContact/suggestion row.
EXTRACTOR_VERSION = "contact-harvest-v1"

_PHONE_RE = re.compile(r"(\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4})")
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

# Ordered (most-specific-first) label -> role matchers. Matched against the
# AI key finding's `label` (e.g. "Emergency Contact", "Healthcare Proxy"),
# never against free document text directly -- the document-intelligence
# extraction step has already isolated candidate label/value pairs and
# tied each to a verbatim excerpt.
_LABEL_ROLE_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"emergency\s*contact", re.I), "EMERGENCY_CONTACT"),
    (re.compile(r"responsible\s*party", re.I), "RESPONSIBLE_PARTY"),
    (re.compile(r"(durable\s*power\s*of\s*attorney|dpoa|power\s*of\s*attorney)", re.I), "DPOA"),
    (
        re.compile(
            r"(healthcare\s*(agent|proxy)|health\s*care\s*(agent|proxy)|advance\s*directive\s*agent)",
            re.I,
        ),
        "HEALTHCARE_AGENT",
    ),
    (re.compile(r"decision\s*maker", re.I), "DECISION_MAKER"),
    (re.compile(r"conservator", re.I), "CONSERVATOR"),
    (re.compile(r"guardian", re.I), "GUARDIAN"),
    (re.compile(r"(primary\s*care\s*giver|primary\s*caregiver)", re.I), "PRIMARY_CAREGIVER"),
]


def _role_for_label(label: str) -> str | None:
    for pattern, role in _LABEL_ROLE_PATTERNS:
        if pattern.search(label):
            return role
    return None


def _parse_contact_value(raw_value: str) -> dict[str, str | None]:
    """Best-effort split of a free-text AI finding value into
    name/relationship/phone/email/address. Never raises; any component
    that cannot be confidently isolated is left None rather than guessed.
    """

    text = (raw_value or "").strip()
    if not text:
        return {
            "name": None,
            "relationship_to_patient": None,
            "phone": None,
            "email": None,
            "address": None,
        }

    phone_match = _PHONE_RE.search(text)
    phone = phone_match.group(1).strip() if phone_match else None
    if phone_match:
        text = (text[: phone_match.start()] + text[phone_match.end() :]).strip(" ,-\u2013")

    email_match = _EMAIL_RE.search(text)
    email = email_match.group(0).strip() if email_match else None
    if email_match:
        text = (text[: email_match.start()] + text[email_match.end() :]).strip(" ,-\u2013")

    relationship = None
    name = text or None

    paren_match = re.search(r"\(([^)]+)\)", text)
    if paren_match:
        relationship = paren_match.group(1).strip() or None
        name = (text[: paren_match.start()] + text[paren_match.end() :]).strip(" ,-\u2013") or None
    elif "-" in text and text.count("-") == 1:
        left, right = (part.strip() for part in text.split("-", 1))
        if left and right:
            name, relationship = left, right
    elif "," in text:
        left, right = (part.strip() for part in text.split(",", 1))
        if left and right and len(right.split()) <= 3:
            name, relationship = left, right

    return {
        "name": name,
        "relationship_to_patient": relationship,
        "phone": phone,
        "email": email,
        "address": None,
    }


def _queue_suggestion(
    db: Session,
    *,
    tenant_id,
    patient_id,
    role: str,
    field_name: str,
    current_value,
    suggested_value,
    document: DocumentRecord,
    now: datetime,
) -> None:
    existing = (
        db.query(PatientContactSuggestion)
        .filter(
            PatientContactSuggestion.tenant_id == tenant_id,
            PatientContactSuggestion.patient_id == patient_id,
            PatientContactSuggestion.role == role,
            PatientContactSuggestion.field_name == field_name,
            PatientContactSuggestion.suggested_value == str(suggested_value),
            PatientContactSuggestion.status == "pending",
        )
        .first()
    )
    if existing is not None:
        return

    db.add(
        PatientContactSuggestion(
            tenant_id=tenant_id,
            patient_id=patient_id,
            role=role,
            field_name=field_name,
            current_value=str(current_value) if current_value is not None else None,
            suggested_value=str(suggested_value),
            source_document_id=document.id,
            source_document_name=document.file_name,
            extractor_version=EXTRACTOR_VERSION,
            extraction_timestamp=now,
            status="pending",
            created_at=now,
            created_by=document.uploaded_by,
        )
    )


def harvest_patient_contacts_from_document(
    db: Session,
    *,
    document: DocumentRecord,
) -> dict[str, list[str]]:
    """
    Scan `document.extracted_values["ai_key_findings"]` for caregiver/
    decision-maker contact data and reconcile it against PatientContact.

    Returns {"applied": [role, ...], "queued": [role, ...]} for
    logging/testing -- never raises for documents with no recognizable
    contact findings (that is the expected, common case).
    """

    result: dict[str, list[str]] = {"applied": [], "queued": []}

    if not document.patient_id or not document.tenant_id:
        return result

    findings = (document.extracted_values or {}).get("ai_key_findings") or []
    if not findings:
        return result

    existing_contacts = get_patient_contacts(
        db, patient_id=document.patient_id, tenant_id=document.tenant_id
    )
    now = datetime.now(timezone.utc)

    for finding in findings:
        label = str(finding.get("label") or "")
        raw_value = str(finding.get("value") or "")
        if not label or not raw_value:
            continue

        role = _role_for_label(label)
        if role is None:
            continue

        parsed = _parse_contact_value(raw_value)
        if not any(parsed.values()):
            continue

        existing_row = existing_contacts.get(role)

        fields_to_apply: dict[str, Any] = {}
        any_conflict = False

        for field_name in ("name", "relationship_to_patient", "phone", "email", "address"):
            new_value = parsed.get(field_name)
            if new_value is None:
                continue

            current_value = getattr(existing_row, field_name, None) if existing_row else None

            if current_value in (None, ""):
                fields_to_apply[field_name] = new_value
                continue

            if str(current_value) == str(new_value):
                continue

            # Conflict: existing non-empty value differs from the
            # harvested value (whether or not it was ever manually
            # overridden) -- never silently overwritten.
            any_conflict = True
            _queue_suggestion(
                db,
                tenant_id=document.tenant_id,
                patient_id=document.patient_id,
                role=role,
                field_name=field_name,
                current_value=current_value,
                suggested_value=new_value,
                document=document,
                now=now,
            )

        if fields_to_apply:
            set_patient_contact(
                db,
                patient_id=document.patient_id,
                tenant_id=document.tenant_id,
                role=role,
                source="DOCUMENT_HARVEST",
                attribution_source=ATTRIBUTION_HARVESTED,
                source_document_id=document.id,
                source_document_name=document.file_name,
                extractor_version=EXTRACTOR_VERSION,
                extraction_timestamp=now,
                updated_by=document.uploaded_by,
                **fields_to_apply,
            )
            if role not in result["applied"]:
                result["applied"].append(role)
            # Refresh so subsequent findings for the same role in this
            # document see the just-applied values rather than re-reading
            # a stale existing_contacts snapshot.
            existing_contacts = get_patient_contacts(
                db, patient_id=document.patient_id, tenant_id=document.tenant_id
            )

        if any_conflict and role not in result["queued"]:
            result["queued"].append(role)

    return result
