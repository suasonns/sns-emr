"""Body Systems correction/amendment infrastructure (compliance
remediation, application blocker A).

Workflow -- identical in shape to `app/services/rnica_amendment_service.py`
(SECTION 12 Amendment Infrastructure), applied to `SystemAssessment` rows
instead of locked RN ICA assessments:

    Clinician/patient/representative/QA submits an amendment (with a
    request_source noting who originated the request)
        -> status = PENDING
        -> Review authority (reuses AMENDMENT_APPROVAL_ROLES from
           app/api/visits.py -- DPCS/DPCS Designee/Case Manager/Supervisor/
           Admin/QA/System) decides
        -> APPROVED or DENIED
        -> Decision logged: decision_user_id/decision_timestamp always;
           decision_reason required for DENIED, optional for APPROVED
        -> Original SystemAssessment content preserved -- the amendment
           stays a linked, separate row; `proposed_value` is never
           auto-applied back onto the original fields.

Every submission and decision is mirrored to the existing audit_event
framework, matching the RNICA amendment workflow and Body Systems' own
save-path auditing.

Body Systems assessments are presently draft-only in this milestone (no
sign/record/finalize endpoint exists yet beyond the `status` column
itself -- see app/models/body_systems.py ASSESSMENT_STATUSES). This
workflow does not replace ordinary draft editing; it is the mechanism
that governs corrections once a `SystemAssessment`'s parent
`BodySystemsAssessment.status` leaves "draft" (enforced in
app/api/routes/body_systems.py's save handler), and is available now so
that boundary can be enforced without a second migration later.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.body_systems_amendment import (
    AMENDMENT_CATEGORIES,
    AMENDMENT_REASON_CODES,
    AMENDMENT_REQUEST_SOURCES,
    BodySystemsAmendment,
)
from app.services.audit_events import audit_event


class BodySystemsAmendmentError(Exception):
    """Raised for validation/not-found/authorization errors."""


def _serialize(record: BodySystemsAmendment) -> dict:
    return {
        "id": str(record.id),
        "tenantId": str(record.tenant_id) if record.tenant_id else None,
        "patientId": str(record.patient_id),
        "systemAssessmentId": str(record.system_assessment_id),
        "system": record.system,
        "fieldReference": record.field_reference,
        "amendmentCategory": record.amendment_category,
        "reasonCode": record.reason_code,
        "requestedChange": record.requested_change,
        "originalValueSnapshot": record.original_value_snapshot,
        "proposedValue": record.proposed_value,
        "requestSource": record.request_source,
        "status": record.status,
        "createdBy": str(record.created_by) if record.created_by else None,
        "createdAt": record.created_at.isoformat() if record.created_at else None,
        "decisionUserId": str(record.decision_user_id) if record.decision_user_id else None,
        "decisionTimestamp": record.decision_timestamp.isoformat() if record.decision_timestamp else None,
        "decisionReason": record.decision_reason,
    }


def create_amendment(
    db: Session,
    *,
    tenant_id,
    patient_id,
    system_assessment_id,
    system: str,
    user_id,
    field_reference: Optional[str],
    amendment_category: str,
    reason_code: str,
    requested_change: str,
    request_source: str = "STAFF",
    original_value_snapshot: Optional[Any] = None,
    proposed_value: Optional[Any] = None,
) -> dict:
    amendment_category = (amendment_category or "").strip().upper()
    if amendment_category not in AMENDMENT_CATEGORIES:
        raise BodySystemsAmendmentError(
            f"amendment_category must be one of {', '.join(AMENDMENT_CATEGORIES)}"
        )

    reason_code = (reason_code or "").strip().upper()
    if reason_code not in AMENDMENT_REASON_CODES:
        raise BodySystemsAmendmentError(
            f"reason_code must be one of {', '.join(AMENDMENT_REASON_CODES)}"
        )

    request_source = (request_source or "STAFF").strip().upper()
    if request_source not in AMENDMENT_REQUEST_SOURCES:
        raise BodySystemsAmendmentError(
            f"request_source must be one of {', '.join(AMENDMENT_REQUEST_SOURCES)}"
        )

    if not requested_change or not requested_change.strip():
        raise BodySystemsAmendmentError("requested_change must not be blank")

    record = BodySystemsAmendment(
        tenant_id=tenant_id,
        patient_id=patient_id,
        system_assessment_id=system_assessment_id,
        system=system,
        field_reference=(field_reference or "").strip() or None,
        amendment_category=amendment_category,
        reason_code=reason_code,
        requested_change=requested_change.strip(),
        request_source=request_source,
        original_value_snapshot=original_value_snapshot,
        proposed_value=proposed_value,
        status="PENDING",
        created_by=user_id,
    )
    db.add(record)
    db.flush()

    audit_event(
        db=db,
        action="BODY_SYSTEMS_AMENDMENT_SUBMITTED",
        entity_type="body_systems_amendment",
        entity_id=str(record.id),
        user_id=str(user_id) if user_id else None,
        tenant_id=str(tenant_id) if tenant_id else None,
        meta={
            "systemAssessmentId": str(system_assessment_id),
            "system": system,
            "fieldReference": field_reference,
            "amendmentCategory": amendment_category,
            "reasonCode": reason_code,
            "requestSource": request_source,
        },
    )

    db.commit()
    db.refresh(record)
    return _serialize(record)


def list_amendments(db: Session, *, tenant_id, system_assessment_id) -> list[dict]:
    query = db.query(BodySystemsAmendment).filter(
        BodySystemsAmendment.system_assessment_id == system_assessment_id
    )
    if tenant_id is not None:
        query = query.filter(BodySystemsAmendment.tenant_id == tenant_id)

    records = query.order_by(BodySystemsAmendment.created_at.desc()).all()
    return [_serialize(r) for r in records]


def _load_pending(db: Session, *, tenant_id, amendment_id) -> BodySystemsAmendment:
    query = db.query(BodySystemsAmendment).filter(BodySystemsAmendment.id == amendment_id)
    if tenant_id is not None:
        query = query.filter(BodySystemsAmendment.tenant_id == tenant_id)
    record = query.first()
    if record is None:
        raise BodySystemsAmendmentError("Amendment not found")
    if record.status != "PENDING":
        raise BodySystemsAmendmentError(
            f"Amendment has already been {record.status.lower()} and cannot be re-decided."
        )
    return record


def approve_amendment(
    db: Session,
    *,
    tenant_id,
    amendment_id,
    user_id,
    decision_reason: Optional[str] = None,
) -> dict:
    record = _load_pending(db, tenant_id=tenant_id, amendment_id=amendment_id)

    if user_id is not None and record.created_by is not None and str(user_id) == str(record.created_by):
        raise BodySystemsAmendmentError("The submitting clinician cannot approve their own amendment.")

    record.status = "APPROVED"
    record.decision_user_id = user_id
    record.decision_timestamp = datetime.now(timezone.utc)
    record.decision_reason = (decision_reason or "").strip() or None
    db.add(record)
    db.flush()

    audit_event(
        db=db,
        action="BODY_SYSTEMS_AMENDMENT_APPROVED",
        entity_type="body_systems_amendment",
        entity_id=str(record.id),
        user_id=str(user_id) if user_id else None,
        tenant_id=str(tenant_id) if tenant_id else None,
        meta={"systemAssessmentId": str(record.system_assessment_id), "decisionReason": record.decision_reason},
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
    decision_reason: str,
) -> dict:
    if not decision_reason or not decision_reason.strip():
        raise BodySystemsAmendmentError("decision_reason must not be blank")

    record = _load_pending(db, tenant_id=tenant_id, amendment_id=amendment_id)

    if user_id is not None and record.created_by is not None and str(user_id) == str(record.created_by):
        raise BodySystemsAmendmentError("The submitting clinician cannot deny their own amendment.")

    record.status = "DENIED"
    record.decision_user_id = user_id
    record.decision_timestamp = datetime.now(timezone.utc)
    record.decision_reason = decision_reason.strip()
    db.add(record)
    db.flush()

    audit_event(
        db=db,
        action="BODY_SYSTEMS_AMENDMENT_DENIED",
        entity_type="body_systems_amendment",
        entity_id=str(record.id),
        user_id=str(user_id) if user_id else None,
        tenant_id=str(tenant_id) if tenant_id else None,
        meta={"systemAssessmentId": str(record.system_assessment_id), "decisionReason": record.decision_reason},
    )

    db.commit()
    db.refresh(record)
    return _serialize(record)
