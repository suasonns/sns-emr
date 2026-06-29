from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.enums import (
    TaskOrigin,
    TaskRegulatoryBasis,
    TaskStatus,
    TaskType,
)
from app.models.task import Task

logger = logging.getLogger(__name__)

ALERT_PREFIX = "MED_RECON"
RECON_REVIEW_REFERENCE_TYPE = "MED_RECON_ITEM"


# =========================================================
# HELPERS
# =========================================================
def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _alert_key(item_id: Any) -> str:
    return f"{ALERT_PREFIX}:{item_id}"


def _pick_enum_member(enum_cls, *candidate_names: str):
    """
    Pick the first enum member that exists.
    Keeps the service resilient across slightly different enum definitions.
    """
    for name in candidate_names:
        if hasattr(enum_cls, name):
            return getattr(enum_cls, name)
    raise ValueError(
        f"{enum_cls.__name__} does not contain any of: {candidate_names}"
    )


def _resolve_created_by_from_session(db: Session):
    """
    Propagate actor context when available.
    created_by is nullable in the live tasks table, so None is allowed.
    """
    raw = db.info.get("user_id")
    if not raw:
        return None

    try:
        return raw if isinstance(raw, uuid.UUID) else uuid.UUID(str(raw))
    except Exception:
        return None


def _set_if_present(obj, **values) -> None:
    """
    Set ORM attributes only if the SQLAlchemy model exposes them.
    This prevents invalid keyword / unmapped attribute crashes.
    """
    for key, value in values.items():
        if hasattr(obj, key):
            setattr(obj, key, value)


def _normalize_completion_reference_type(value: Optional[str]) -> Optional[str]:
    """
    Normalize completion reference type to a DB-allowed value.
    """
    if value is None:
        return None

    normalized = str(value).strip().upper()

    allowed = {"VISIT", "NOTE", "DOCUMENT", "CLINICAL_NOTE"}
    if normalized in allowed:
        return normalized

    if normalized in {"MED_RECON_ITEM", "MED_RECONCILIATION_ITEM"}:
        return "DOCUMENT"

    return "DOCUMENT"


def _extract_match_type(comparison: Any) -> Optional[str]:
    if comparison is None:
        return None

    if isinstance(comparison, dict):
        raw = comparison.get("match_type")
    else:
        raw = getattr(comparison, "match_type", None)

    if raw is None:
        return None

    return str(raw).strip().upper()


def _extract_discrepancy_flags(comparison: Any) -> list[str]:
    if comparison is None:
        return []

    if isinstance(comparison, dict):
        raw = comparison.get("discrepancy_flags") or comparison.get("flags") or []
    else:
        raw = (
            getattr(comparison, "discrepancy_flags", None)
            or getattr(comparison, "flags", None)
            or []
        )

    if raw is None:
        return []

    if isinstance(raw, (list, tuple, set)):
        return [str(x) for x in raw if x is not None]

    return [str(raw)]


def _comparison_requires_task(comparison: Any) -> bool:
    """
    A task is required when comparison indicates a non-exact match
    or any discrepancy flags are present.
    """
    match_type = _extract_match_type(comparison)
    discrepancy_flags = _extract_discrepancy_flags(comparison)

    if match_type in {"NO_MATCH", "PARTIAL_MATCH", "CONFLICT"}:
        return True

    if discrepancy_flags:
        return True

    return False


# =========================================================
# LOOKUP OPEN TASK
# =========================================================
def get_open_reconciliation_review_task_for_item(
    *,
    db: Session,
    reconciliation_item_id,
    tenant_id=None,
    patient_id=None,
) -> Optional[Task]:
    """
    Return the existing open reconciliation review task for a specific
    med reconciliation item if one already exists.
    """
    alert_reason = _alert_key(reconciliation_item_id)

    active_statuses = []
    for candidate in ("PENDING", "IN_PROGRESS", "OVERDUE"):
        if hasattr(TaskStatus, candidate):
            active_statuses.append(getattr(TaskStatus, candidate))

    query = (
        db.query(Task)
        .filter(Task.alert_reason == alert_reason)
        .filter(Task.status.in_(active_statuses))
    )

    if tenant_id is not None and hasattr(Task, "tenant_id"):
        query = query.filter(Task.tenant_id == tenant_id)

    if patient_id is not None and hasattr(Task, "patient_id"):
        query = query.filter(Task.patient_id == patient_id)

    return query.order_by(Task.created_at.asc()).first()


# =========================================================
# CREATE TASK
# =========================================================
def create_reconciliation_task_if_needed(
    *,
    db: Session,
    tenant_id,
    patient_id,
    import_id: Optional[Any] = None,
    item_id: Optional[Any] = None,
    comparison: Optional[Any] = None,
    reconciliation_item_id: Optional[Any] = None,
    review_reason: Optional[str] = None,
):
    """
    Import-flow-safe adapter used by med reconciliation import service.

    Supports both call styles:
    - create_reconciliation_task_if_needed(..., item_id=..., comparison=...)
    - create_reconciliation_task_if_needed(..., reconciliation_item_id=..., review_reason=...)

    Behavior:
    - creates exactly one active task per reconciliation item
    - suppresses task creation when comparison is an exact/no-flag match
    - avoids invalid ORM keyword crashes by only setting optional attributes if present
    - leaves transaction ownership to caller (does NOT commit)
    """
    effective_item_id = item_id if item_id is not None else reconciliation_item_id
    if effective_item_id is None:
        logger.info("MED_RECON_TASK: skipped because no item id was provided")
        return None

    if comparison is not None and not _comparison_requires_task(comparison):
        logger.info(
            "MED_RECON_TASK: skipped because comparison does not require review item_id=%s",
            str(effective_item_id),
        )
        return None

    now = _utcnow()
    due_at = now + timedelta(hours=24)
    alert_reason = _alert_key(effective_item_id)

    task_type = _pick_enum_member(
        TaskType,
        "CLINICAL_REVIEW_REQUIRED",
        "MED_RECON_REVIEW",
        "REVIEW",
    )

    pending_status = _pick_enum_member(
        TaskStatus,
        "PENDING",
    )

    active_statuses = []
    for candidate in ("PENDING", "IN_PROGRESS", "OVERDUE"):
        if hasattr(TaskStatus, candidate):
            active_statuses.append(getattr(TaskStatus, candidate))

    origin_value = _pick_enum_member(
        TaskOrigin,
        "SYSTEM",
    )

    regulatory_basis_value = _pick_enum_member(
        TaskRegulatoryBasis,
        "CLINICAL_REVIEW",
        "MEDICATION_RECONCILIATION",
        "CONDITION_TRIGGER",
    )

    existing = (
        db.query(Task)
        .filter(Task.tenant_id == tenant_id)
        .filter(Task.patient_id == patient_id)
        .filter(Task.alert_reason == alert_reason)
        .filter(Task.task_type == task_type)
        .filter(Task.status.in_(active_statuses))
        .first()
    )

    if existing:
        logger.info(
            "MED_RECON_TASK: existing active task reused task_id=%s item_id=%s import_id=%s",
            str(existing.id),
            str(effective_item_id),
            str(import_id) if import_id else None,
        )
        return existing

    created_by = _resolve_created_by_from_session(db)

    task = Task(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        task_type=task_type,
        origin=origin_value,
        discipline="RN",
        regulatory_basis=regulatory_basis_value,
        due_date=due_at.date(),
        status=pending_status,
        created_at=now,
        updated_at=now,
        created_by=created_by,
    )

    _set_if_present(
        task,
        due_at=due_at,
        sla_start_at=now,
        sla_due_at=due_at,
        alert_reason=alert_reason,
        reference_type=RECON_REVIEW_REFERENCE_TYPE,
        reference_id=effective_item_id,
        assigned_role="RN",
        priority="HIGH",
        clinical_severity="MODERATE",
        escalation_level=0,
        notification_required=False,
        is_overdue=False,
        escalation_reason=review_reason or "Medication reconciliation review required",
        assigned_user_id=None,
        benefit_period_id=None,
        completed_at=None,
        completion_reference_type=None,
        completion_reference_id=None,
        excused_reason_code=None,
        excused_at=None,
        excused_source=None,
        scheduled_start_at=None,
        schedule_status=None,
        clinical_note_id=None,
        incident_id=None,
        requires_countersignature=False,
        countersigned_by=None,
        countersigned_at=None,
        escalated_at=None,
    )

    db.add(task)
    db.flush()

    logger.info(
        "MED_RECON_TASK: created task_id=%s item_id=%s patient_id=%s import_id=%s review_reason=%s",
        str(task.id),
        str(effective_item_id),
        str(patient_id),
        str(import_id) if import_id else None,
        review_reason,
    )

    return task


# =========================================================
# COMPLETE TASK
# =========================================================
def complete_reconciliation_review_task_if_exists(
    *,
    db: Session,
    reconciliation_item_id,
    completion_reference_type: Optional[str],
    completion_reference_id,
):
    """
    Complete the reconciliation review task when reconciliation review is finished.

    Behavior:
    - finds only an open task for the given med reconciliation item
    - normalizes completion_reference_type to a DB-allowed value
    - leaves transaction ownership to caller
    """
    alert_reason = _alert_key(reconciliation_item_id)
    now = _utcnow()

    active_statuses = []
    for candidate in ("PENDING", "IN_PROGRESS", "OVERDUE"):
        if hasattr(TaskStatus, candidate):
            active_statuses.append(getattr(TaskStatus, candidate))

    completed_status = _pick_enum_member(
        TaskStatus,
        "COMPLETED",
    )

    task = (
        db.query(Task)
        .filter(Task.alert_reason == alert_reason)
        .filter(Task.status.in_(active_statuses))
        .order_by(Task.created_at.asc())
        .first()
    )

    if not task:
        logger.info(
            "MED_RECON_TASK: no active task found for item_id=%s",
            str(reconciliation_item_id),
        )
        return None

    normalized_completion_reference_type = _normalize_completion_reference_type(
        completion_reference_type
    )

    task.status = completed_status
    task.completed_at = now
    task.updated_at = now

    _set_if_present(
        task,
        completion_reference_type=normalized_completion_reference_type,
        completion_reference_id=completion_reference_id,
        is_overdue=False,
    )

    logger.info(
        "MED_RECON_TASK: completed task_id=%s item_id=%s completion_reference_type=%s completion_reference_id=%s",
        str(task.id),
        str(reconciliation_item_id),
        normalized_completion_reference_type,
        str(completion_reference_id) if completion_reference_id else None,
    )

    return task