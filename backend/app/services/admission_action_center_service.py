# app/services/admission_action_center_service.py
"""Admission Action Center (Phase A) service.

A lightweight, dedicated request/status tracker for actions raised during
RN ICA documentation: Medication Request, Physician Order, DME Order,
Supply Order, and Referral. Reachable from every RN ICA section without
navigating away from the assessment (the UI opens it as a modal/drawer).

Deliberately simple by design (Phase A scope):
- No approval routing (that's `physician_orders` / `PhysicianOrder`).
- No fulfillment workflow (that's `patient_orders` / `PatientOrder`).
- No notifications.
- Linear status tracking only:
  REQUESTED -> ORDERED -> SENT -> ACKNOWLEDGED -> DELIVERED -> COMPLETED.

Every status change is appended to `status_history` (mirrors the
Section 11.C `evidence_sources` pattern) and mirrored to the existing
audit_event framework for tenant-wide audit visibility.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.admission_action_request import (
    ADMISSION_ACTION_REQUEST_STATUSES,
    ADMISSION_ACTION_REQUEST_TYPES,
    AdmissionActionRequest,
)
from app.services.audit_events import audit_event


class AdmissionActionCenterError(Exception):
    """Raised for validation/not-found errors in the Admission Action Center."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _history_entry(status: str, user_id: Optional[str], note: Optional[str] = None) -> dict:
    entry: dict[str, Any] = {
        "status": status,
        "changed_by": str(user_id) if user_id else None,
        "changed_at": _now_iso(),
    }
    if note:
        entry["note"] = note
    return entry


def _serialize(request: AdmissionActionRequest) -> dict:
    return {
        "id": str(request.id),
        "tenantId": str(request.tenant_id) if request.tenant_id else None,
        "patientId": str(request.patient_id),
        "rnicaAssessmentId": str(request.rnica_assessment_id) if request.rnica_assessment_id else None,
        "sourceSection": request.source_section,
        "requestType": request.request_type,
        "status": request.status,
        "details": request.details,
        "statusHistory": request.status_history or [],
        "createdBy": str(request.created_by) if request.created_by else None,
        "createdAt": request.created_at.isoformat() if request.created_at else None,
        "updatedBy": str(request.updated_by) if request.updated_by else None,
        "updatedAt": request.updated_at.isoformat() if request.updated_at else None,
    }


def create_request(
    db: Session,
    *,
    tenant_id,
    patient_id,
    user_id,
    request_type: str,
    details: str,
    rnica_assessment_id: Optional[UUID] = None,
    source_section: Optional[str] = None,
) -> dict:
    request_type = (request_type or "").strip().upper()
    if request_type not in ADMISSION_ACTION_REQUEST_TYPES:
        raise AdmissionActionCenterError(
            f"request_type must be one of {', '.join(ADMISSION_ACTION_REQUEST_TYPES)}"
        )

    if not details or not details.strip():
        raise AdmissionActionCenterError("details must not be blank")

    record = AdmissionActionRequest(
        tenant_id=tenant_id,
        patient_id=patient_id,
        rnica_assessment_id=rnica_assessment_id,
        source_section=source_section,
        request_type=request_type,
        status="REQUESTED",
        details=details.strip(),
        created_by=user_id,
        status_history=[_history_entry("REQUESTED", user_id, note="Request created")],
    )
    db.add(record)
    db.flush()

    audit_event(
        db=db,
        action="ADMISSION_ACTION_REQUEST_CREATED",
        entity_type="admission_action_request",
        entity_id=str(record.id),
        user_id=str(user_id) if user_id else None,
        tenant_id=str(tenant_id) if tenant_id else None,
        meta={
            "patientId": str(patient_id),
            "requestType": request_type,
            "sourceSection": source_section,
        },
    )

    db.commit()
    db.refresh(record)
    return _serialize(record)


def list_requests(db: Session, *, tenant_id, patient_id) -> list[dict]:
    query = db.query(AdmissionActionRequest).filter(
        AdmissionActionRequest.patient_id == patient_id
    )
    if tenant_id is not None:
        query = query.filter(AdmissionActionRequest.tenant_id == tenant_id)

    records = query.order_by(AdmissionActionRequest.created_at.desc()).all()
    return [_serialize(r) for r in records]


def update_status(
    db: Session,
    *,
    tenant_id,
    request_id,
    user_id,
    new_status: str,
    note: Optional[str] = None,
) -> dict:
    new_status = (new_status or "").strip().upper()
    if new_status not in ADMISSION_ACTION_REQUEST_STATUSES:
        raise AdmissionActionCenterError(
            f"status must be one of {', '.join(ADMISSION_ACTION_REQUEST_STATUSES)}"
        )

    query = db.query(AdmissionActionRequest).filter(AdmissionActionRequest.id == request_id)
    if tenant_id is not None:
        query = query.filter(AdmissionActionRequest.tenant_id == tenant_id)
    record = query.first()
    if record is None:
        raise AdmissionActionCenterError("Admission action request not found")

    previous_status = record.status
    record.status = new_status
    record.updated_by = user_id
    history = list(record.status_history or [])
    history.append(_history_entry(new_status, user_id, note=note))
    record.status_history = history
    db.add(record)
    db.flush()

    audit_event(
        db=db,
        action="ADMISSION_ACTION_REQUEST_STATUS_CHANGED",
        entity_type="admission_action_request",
        entity_id=str(record.id),
        user_id=str(user_id) if user_id else None,
        tenant_id=str(tenant_id) if tenant_id else None,
        meta={
            "previousStatus": previous_status,
            "newStatus": new_status,
            "note": note,
        },
    )

    db.commit()
    db.refresh(record)
    return _serialize(record)
