from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.models.rnica_assessment import RnicaAssessment

HOPE_STATUS_OPEN = "OPEN"
HOPE_STATUS_CLOSED = "CLOSED"
HOPE_STATUS_READY_TO_EXPORT = "READY_TO_EXPORT"
HOPE_STATUS_EXPORTED_TO_BATCH = "EXPORTED_TO_BATCH"
HOPE_STATUS_SUBMITTED = "SUBMITTED"
HOPE_STATUS_INACTIVATED = "INACTIVATED"

HOPE_WORKFLOW_STATUSES = {
    HOPE_STATUS_OPEN,
    HOPE_STATUS_CLOSED,
    HOPE_STATUS_READY_TO_EXPORT,
    HOPE_STATUS_EXPORTED_TO_BATCH,
    HOPE_STATUS_SUBMITTED,
    HOPE_STATUS_INACTIVATED,
}


class HopeWorkflowError(ValueError):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _require_locked(record: RnicaAssessment) -> None:
    if not record.locked:
        raise HopeWorkflowError("HOPE workflow actions require a locked assessment.")


def _sync_form_data_submission_fields(record: RnicaAssessment) -> None:
    form_data = dict(record.form_data or {})
    finalization = dict(form_data.get("finalization") or {})
    finalization["hopeSubmissionNumber"] = record.hope_submission_number or ""
    finalization["hopeAlreadySubmitted"] = bool(record.hope_already_submitted)
    form_data["finalization"] = finalization
    record.form_data = form_data


def derive_status(record: RnicaAssessment) -> str:
    if record.hope_inactivated:
        return HOPE_STATUS_INACTIVATED
    if record.hope_submission_number or record.hope_already_submitted:
        return HOPE_STATUS_SUBMITTED
    if record.hope_exported_to_batch_at or record.hope_export_batch_id:
        return HOPE_STATUS_EXPORTED_TO_BATCH
    if record.hope_ready_at:
        return HOPE_STATUS_READY_TO_EXPORT
    status = str(record.hope_workflow_status or "").strip().upper()
    if status == HOPE_STATUS_OPEN:
        return HOPE_STATUS_OPEN
    if record.hope_closed_at:
        return HOPE_STATUS_CLOSED
    return HOPE_STATUS_OPEN


def _persist_status(record: RnicaAssessment) -> str:
    status = derive_status(record)
    record.hope_workflow_status = status
    return status


def current_metadata(record: RnicaAssessment) -> dict[str, Any]:
    status = _persist_status(record)
    return {
        "status": status,
        "closedAt": record.hope_closed_at.isoformat() if record.hope_closed_at else None,
        "readyAt": record.hope_ready_at.isoformat() if record.hope_ready_at else None,
        "exportedToBatchAt": record.hope_exported_to_batch_at.isoformat() if record.hope_exported_to_batch_at else None,
        "exportBatchId": record.hope_export_batch_id,
        "submissionNumber": record.hope_submission_number,
        "alreadySubmitted": bool(record.hope_already_submitted),
        "submittedAt": record.hope_submitted_at.isoformat() if record.hope_submitted_at else None,
        "inactivated": bool(record.hope_inactivated),
        "inactivatedAt": record.hope_inactivated_at.isoformat() if record.hope_inactivated_at else None,
        "unlockedAt": record.hope_unlocked_at.isoformat() if record.hope_unlocked_at else None,
        "unlockReason": record.hope_unlock_reason,
    }


def sync_submission_fields_from_form_data(record: RnicaAssessment, form_data: dict[str, Any] | None) -> None:
    finalization = ((form_data or {}).get("finalization") or {})
    record.hope_submission_number = _normalize_text(finalization.get("hopeSubmissionNumber"))
    record.hope_already_submitted = bool(finalization.get("hopeAlreadySubmitted"))
    _sync_form_data_submission_fields(record)
    if record.locked:
        _persist_status(record)
    else:
        record.hope_workflow_status = HOPE_STATUS_OPEN


def apply_close(record: RnicaAssessment, *, user_id) -> dict[str, Any]:
    _require_locked(record)
    if record.hope_inactivated:
        raise HopeWorkflowError("Inactivated HOPE records must be reactivated before closing.")
    if not record.hope_closed_at:
        record.hope_closed_at = _utcnow()
        record.hope_closed_by = user_id
    if derive_status(record) == HOPE_STATUS_OPEN:
        record.hope_workflow_status = HOPE_STATUS_CLOSED
    return current_metadata(record)


def apply_ready_to_export(record: RnicaAssessment, *, user_id) -> dict[str, Any]:
    _require_locked(record)
    if record.hope_inactivated:
        raise HopeWorkflowError("Inactivated HOPE records cannot be marked ready to export.")
    apply_close(record, user_id=user_id)
    if not record.hope_ready_at:
        record.hope_ready_at = _utcnow()
        record.hope_ready_by = user_id
    if derive_status(record) in {HOPE_STATUS_OPEN, HOPE_STATUS_CLOSED}:
        record.hope_workflow_status = HOPE_STATUS_READY_TO_EXPORT
    return current_metadata(record)


def apply_export_to_batch(record: RnicaAssessment, *, user_id, batch_id: str | None = None) -> dict[str, Any]:
    _require_locked(record)
    if record.hope_inactivated:
        raise HopeWorkflowError("Inactivated HOPE records cannot be exported to batch.")
    apply_ready_to_export(record, user_id=user_id)
    if record.hope_submission_number or record.hope_already_submitted:
        raise HopeWorkflowError("Submitted HOPE records cannot be added to a new export batch.")
    if not record.hope_export_batch_id:
        record.hope_export_batch_id = _normalize_text(batch_id) or f"HOPE-{str(record.id)[:8]}"
    if not record.hope_exported_to_batch_at:
        record.hope_exported_to_batch_at = _utcnow()
        record.hope_exported_to_batch_by = user_id
    record.hope_workflow_status = HOPE_STATUS_EXPORTED_TO_BATCH
    return current_metadata(record)


def apply_submission_update(
    record: RnicaAssessment,
    *,
    user_id,
    submission_number: str | None,
    already_submitted: bool,
) -> dict[str, Any]:
    _require_locked(record)
    normalized_submission_number = _normalize_text(submission_number)
    if normalized_submission_number and record.hope_inactivated:
        raise HopeWorkflowError("Inactivated HOPE records cannot be marked submitted.")
    record.hope_submission_number = normalized_submission_number
    record.hope_already_submitted = bool(already_submitted)
    _sync_form_data_submission_fields(record)
    if record.hope_submission_number or record.hope_already_submitted:
        if not record.hope_submitted_at:
            record.hope_submitted_at = _utcnow()
            record.hope_submitted_by = user_id
        record.hope_workflow_status = HOPE_STATUS_SUBMITTED
    else:
        record.hope_submitted_at = None
        record.hope_submitted_by = None
        _persist_status(record)
    return current_metadata(record)


def apply_inactivation(record: RnicaAssessment, *, user_id, inactivated: bool) -> dict[str, Any]:
    _require_locked(record)
    record.hope_inactivated = bool(inactivated)
    if record.hope_inactivated:
        if not record.hope_inactivated_at:
            record.hope_inactivated_at = _utcnow()
            record.hope_inactivated_by = user_id
        record.hope_workflow_status = HOPE_STATUS_INACTIVATED
    else:
        record.hope_inactivated_at = None
        record.hope_inactivated_by = None
        _persist_status(record)
    return current_metadata(record)


def apply_unlock(record: RnicaAssessment, *, user_id, reason: str) -> dict[str, Any]:
    _require_locked(record)
    normalized_reason = _normalize_text(reason)
    if not normalized_reason:
        raise HopeWorkflowError("Unlock reason is required.")
    if record.hope_submission_number or record.hope_already_submitted:
        raise HopeWorkflowError("Submitted HOPE records cannot be unlocked. Clear submission tracking first if this was entered in error.")
    record.hope_workflow_status = HOPE_STATUS_OPEN
    record.hope_ready_at = None
    record.hope_ready_by = None
    record.hope_exported_to_batch_at = None
    record.hope_exported_to_batch_by = None
    record.hope_export_batch_id = None
    record.hope_inactivated = False
    record.hope_inactivated_at = None
    record.hope_inactivated_by = None
    record.hope_unlocked_at = _utcnow()
    record.hope_unlocked_by = user_id
    record.hope_unlock_reason = normalized_reason
    return current_metadata(record)
