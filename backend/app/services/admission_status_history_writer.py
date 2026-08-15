from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.admission_status_history import AdmissionStatusHistory


def write_admission_status_history(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    changed_by: UUID,
    new_status: str,
    previous_status: str | None = None,
    admission_id: UUID | None = None,
    reason: str | None = None,
    notes: str | None = None,
    changed_at: datetime | None = None,
    flush: bool = True,
    skip_if_same_transition: bool = True,
) -> AdmissionStatusHistory | None:
    """
    Write one admission status audit record.

    Returns:
        AdmissionStatusHistory instance, or None if the write is skipped
        because the transition is identical to the latest history row.
    """

    if not new_status or not str(new_status).strip():
        raise ValueError("new_status is required")

    if not tenant_id:
        raise ValueError("tenant_id is required")

    if not patient_id:
        raise ValueError("patient_id is required")

    if not changed_by:
        raise ValueError("changed_by is required")

    normalized_new_status = str(new_status).strip()

    event_time = changed_at or datetime.now(timezone.utc)
    if event_time.tzinfo is None:
        event_time = event_time.replace(tzinfo=timezone.utc)

    if skip_if_same_transition:
        latest = (
            db.query(AdmissionStatusHistory)
            .filter(
                AdmissionStatusHistory.tenant_id == tenant_id,
                AdmissionStatusHistory.patient_id == patient_id,
            )
            .order_by(AdmissionStatusHistory.changed_at.desc())
            .first()
        )

        if latest:
            same_prev = latest.previous_status == previous_status
            same_new = latest.new_status == normalized_new_status
            same_admission = latest.admission_id == admission_id

            if same_prev and same_new and same_admission:
                return None

    history = AdmissionStatusHistory(
        tenant_id=tenant_id,
        patient_id=patient_id,
        admission_id=admission_id,
        previous_status=previous_status,
        new_status=normalized_new_status,
        changed_by=changed_by,
        changed_at=event_time,
        reason=reason.strip() if isinstance(reason, str) and reason.strip() else None,
        notes=notes.strip() if isinstance(notes, str) and notes.strip() else None,
    )

    db.add(history)

    if flush:
        db.flush()

    return history
