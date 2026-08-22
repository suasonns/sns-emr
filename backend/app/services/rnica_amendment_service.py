# app/services/rnica_amendment_service.py
"""SECTION 12 -- Amendment Infrastructure.

A distinct, timestamped, attributable correction/addendum workflow for an
already-locked (signed) RN ICA assessment, per the frozen master map's
"Correction / amendment path". This is deliberately NOT the same thing as
editing `rnica_assessments.form_data`: a locked assessment's original
content is never mutated by this workflow, regardless of amendment
outcome.

Workflow:
    RN/Clinician submits amendment
        -> status = PENDING
        -> Review authority (DPCS / DPCS Designee / Case Manager
           Supervisor -- see AMENDMENT_APPROVAL_ROLES in app/api/visits.py)
           evaluates
        -> APPROVED or DENIED
        -> Decision logged (approved_by/approved_at or denied_reason)
        -> Original record preserved -- the amendment stays a linked,
           separate row; `proposed_value` is never auto-applied back onto
           the signed content.

Every submission and decision is mirrored to the existing audit_event
framework, matching Admission Action Center / Merge Duplicate Problems.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.rnica_amendment import (
    AMENDMENT_CATEGORIES,
    AMENDMENT_REASON_CODES,
    RnicaAmendment,
)
from app.services.audit_events import audit_event


class RnicaAmendmentError(Exception):
    """Raised for validation/not-found/authorization errors."""


def _serialize(record: RnicaAmendment) -> dict:
    return {
        "id": str(record.id),
        "tenantId": str(record.tenant_id) if record.tenant_id else None,
        "patientId": str(record.patient_id),
        "assessmentId": str(record.rnica_assessment_id),
        "sectionReference": record.section_reference,
        "amendmentCategory": record.amendment_category,
        "reasonCode": record.reason_code,
        "requestedChange": record.requested_change,
        "originalValueSnapshot": record.original_value_snapshot,
        "proposedValue": record.proposed_value,
        "status": record.status,
        "createdBy": str(record.created_by) if record.created_by else None,
        "createdAt": record.created_at.isoformat() if record.created_at else None,
        "approvedBy": str(record.approved_by) if record.approved_by else None,
        "approvedAt": record.approved_at.isoformat() if record.approved_at else None,
        "deniedReason": record.denied_reason,
    }


def create_amendment(
    db: Session,
    *,
    tenant_id,
    patient_id,
    rnica_assessment_id,
    user_id,
    section_reference: Optional[str],
    amendment_category: str,
    reason_code: str,
    requested_change: str,
    original_value_snapshot: Optional[Any] = None,
    proposed_value: Optional[Any] = None,
) -> dict:
    amendment_category = (amendment_category or "").strip().upper()
    if amendment_category not in AMENDMENT_CATEGORIES:
        raise RnicaAmendmentError(
            f"amendment_category must be one of {', '.join(AMENDMENT_CATEGORIES)}"
        )

    reason_code = (reason_code or "").strip().upper()
    if reason_code not in AMENDMENT_REASON_CODES:
        raise RnicaAmendmentError(
            f"reason_code must be one of {', '.join(AMENDMENT_REASON_CODES)}"
        )

    if not requested_change or not requested_change.strip():
        raise RnicaAmendmentError("requested_change must not be blank")

    record = RnicaAmendment(
        tenant_id=tenant_id,
        patient_id=patient_id,
        rnica_assessment_id=rnica_assessment_id,
        section_reference=(section_reference or "").strip() or None,
        amendment_category=amendment_category,
        reason_code=reason_code,
        requested_change=requested_change.strip(),
        original_value_snapshot=original_value_snapshot,
        proposed_value=proposed_value,
        status="PENDING",
        created_by=user_id,
    )
    db.add(record)
    db.flush()

    audit_event(
        db=db,
        action="RNICA_AMENDMENT_SUBMITTED",
        entity_type="rnica_amendment",
        entity_id=str(record.id),
        user_id=str(user_id) if user_id else None,
        tenant_id=str(tenant_id) if tenant_id else None,
        meta={
            "assessmentId": str(rnica_assessment_id),
            "sectionReference": section_reference,
            "amendmentCategory": amendment_category,
            "reasonCode": reason_code,
        },
    )

    db.commit()
    db.refresh(record)
    return _serialize(record)


def list_amendments(db: Session, *, tenant_id, rnica_assessment_id) -> list[dict]:
    query = db.query(RnicaAmendment).filter(
        RnicaAmendment.rnica_assessment_id == rnica_assessment_id
    )
    if tenant_id is not None:
        query = query.filter(RnicaAmendment.tenant_id == tenant_id)

    records = query.order_by(RnicaAmendment.created_at.desc()).all()
    return [_serialize(r) for r in records]


def _load_pending(db: Session, *, tenant_id, amendment_id) -> RnicaAmendment:
    query = db.query(RnicaAmendment).filter(RnicaAmendment.id == amendment_id)
    if tenant_id is not None:
        query = query.filter(RnicaAmendment.tenant_id == tenant_id)
    record = query.first()
    if record is None:
        raise RnicaAmendmentError("Amendment not found")
    if record.status != "PENDING":
        raise RnicaAmendmentError(f"Amendment has already been {record.status.lower()} and cannot be re-decided.")
    return record


def approve_amendment(
    db: Session,
    *,
    tenant_id,
    amendment_id,
    user_id,
) -> dict:
    record = _load_pending(db, tenant_id=tenant_id, amendment_id=amendment_id)

    if user_id is not None and record.created_by is not None and str(user_id) == str(record.created_by):
        raise RnicaAmendmentError("The submitting clinician cannot approve their own amendment.")

    record.status = "APPROVED"
    record.approved_by = user_id
    record.approved_at = datetime.now(timezone.utc)
    db.add(record)
    db.flush()

    audit_event(
        db=db,
        action="RNICA_AMENDMENT_APPROVED",
        entity_type="rnica_amendment",
        entity_id=str(record.id),
        user_id=str(user_id) if user_id else None,
        tenant_id=str(tenant_id) if tenant_id else None,
        meta={"assessmentId": str(record.rnica_assessment_id)},
    )

    db.commit()
    db.refresh(record)
    return _serialize(record)


def deny_amendment(
    db: Session,
    *,
    tenant_id,
    amendment_id,
    user_id,
    denied_reason: str,
) -> dict:
    if not denied_reason or not denied_reason.strip():
        raise RnicaAmendmentError("denied_reason must not be blank")

    record = _load_pending(db, tenant_id=tenant_id, amendment_id=amendment_id)

    if user_id is not None and record.created_by is not None and str(user_id) == str(record.created_by):
        raise RnicaAmendmentError("The submitting clinician cannot deny their own amendment.")

    record.status = "DENIED"
    record.approved_by = user_id
    record.approved_at = datetime.now(timezone.utc)
    record.denied_reason = denied_reason.strip()
    db.add(record)
    db.flush()

    audit_event(
        db=db,
        action="RNICA_AMENDMENT_DENIED",
        entity_type="rnica_amendment",
        entity_id=str(record.id),
        user_id=str(user_id) if user_id else None,
        tenant_id=str(tenant_id) if tenant_id else None,
        meta={"assessmentId": str(record.rnica_assessment_id), "deniedReason": record.denied_reason},
    )

    db.commit()
    db.refresh(record)
    return _serialize(record)
