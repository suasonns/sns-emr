from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.med_reconciliation import MedReconciliationItem
from app.models.task import Task
from app.models.enums import TaskStatus

logger = logging.getLogger(__name__)

UNRESOLVED_REVIEW_STATUSES = {"PENDING"}
DUPLICATE_SUPERSEDED_NOTE_PREFIX = "[AUTO-SUPERSEDED DUPLICATE]"


# =========================================================
# HELPERS
# =========================================================

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _set_if_present(obj, **values) -> None:
    """
    Set ORM attributes only if the SQLAlchemy model exposes them.
    This avoids invalid/missing attribute crashes across environments.
    """
    for key, value in values.items():
        if hasattr(obj, key):
            setattr(obj, key, value)


def _pick_task_status(*candidate_names: str):
    """
    Resolve the first available TaskStatus enum member.
    Falls back conservatively to COMPLETED if EXCUSED/CANCELLED
    are not present in the environment.
    """
    for name in candidate_names:
        if hasattr(TaskStatus, name):
            return getattr(TaskStatus, name)
    raise ValueError(
        f"TaskStatus does not contain any of: {candidate_names}"
    )


def _append_note(existing: Optional[str], addition: str) -> str:
    existing_value = (existing or "").strip()
    if not existing_value:
        return addition
    return f"{existing_value}\n{addition}"


# =========================================================
# CORE MAINTENANCE
# =========================================================

def close_older_duplicate_tasks_when_one_duplicate_remains_active(
    *,
    db,
    patient_id,
    med_name_normalized=None,
):
    """
    Safely close older duplicate tasks for same medication.
    ONLY uses med_name_normalized (no undefined variables).
    """

    if not med_name_normalized:
        return None

    try:
        tasks = (
            db.query(Task)
            .filter(Task.patient_id == patient_id)
            .filter(Task.status.in_(["PENDING", "OVERDUE"]))
            .filter(Task.alert_reason.like(f"%{med_name_normalized}%"))
            .order_by(Task.created_at.desc())
            .all()
        )

        if not tasks or len(tasks) <= 1:
            return None

        # Keep newest, close older
        active_task = tasks[0]
        closed_count = 0

        for task in tasks[1:]:
            task.status = "COMPLETED"
            task.completed_at = datetime.utcnow()
            closed_count += 1

        return {
            "active_task_id": str(active_task.id),
            "closed_count": closed_count,
        }

    except Exception as e:
        logger.exception(
            "DEDUP TASK CLEANUP FAILED patient_id=%s med=%s error=%s",
            str(patient_id),
            med_name_normalized,
            str(e),
        )
        return None
    """
    Keep ONE newest unresolved med reconciliation item active for a given
    normalized medication signature and supersede older unresolved duplicates.

    Production behavior:
    - finds unresolved duplicate med reconciliation items by normalized signature
    - keeps the newest unresolved item as the active survivor
    - marks older duplicate items as REJECTED so they stop blocking finalize
    - closes older active duplicate tasks linked to those older duplicate items
    - preserves traceability in item notes and task metadata
    - does NOT commit (caller owns transaction)

    Returns:
        {
            "kept_item_id": str | None,
            "superseded_item_ids": list[str],
            "closed_task_ids": list[str],
        }
    """

    if not med_name_normalized:
        return {
            "kept_item_id": None,
            "superseded_item_ids": [],
            "closed_task_ids": [],
        }

    query = (
        db.query(MedReconciliationItem)
        .filter(MedReconciliationItem.patient_id == patient_id)
        .filter(MedReconciliationItem.review_status.in_(UNRESOLVED_REVIEW_STATUSES))
        .filter(MedReconciliationItem.med_name_normalized == med_name_normalized)
    )

    # Only filter on normalized detail fields if the ORM exposes them
    # and a normalized value is available.
    if hasattr(MedReconciliationItem, "dose_normalized") and dose_normalized is not None:
        query = query.filter(
            getattr(MedReconciliationItem, "dose_normalized") == dose_normalized
        )

    if hasattr(MedReconciliationItem, "route_normalized") and route_normalized is not None:
        query = query.filter(
            getattr(MedReconciliationItem, "route_normalized") == route_normalized
        )

    if hasattr(MedReconciliationItem, "frequency_normalized") and frequency_normalized is not None:
        query = query.filter(
            getattr(MedReconciliationItem, "frequency_normalized") == frequency_normalized
        )

    duplicate_items = (
        query.order_by(
            MedReconciliationItem.created_at.desc(),
            MedReconciliationItem.id.desc(),
        )
        .all()
    )

    if not duplicate_items:
        return {
            "kept_item_id": None,
            "superseded_item_ids": [],
            "closed_task_ids": [],
        }

    if len(duplicate_items) == 1:
        survivor = duplicate_items[0]
        return {
            "kept_item_id": str(survivor.id),
            "superseded_item_ids": [],
            "closed_task_ids": [],
        }

    now = _utcnow()

    survivor = duplicate_items[0]
    older_duplicates = duplicate_items[1:]
    older_duplicate_ids = [item.id for item in older_duplicates]

    logger.info(
        "MED_RECON_DEDUP: survivor_item_id=%s duplicate_count=%s med_name_normalized=%s",
        str(survivor.id),
        len(duplicate_items),
        med_name_normalized,
    )

    # =========================================================
    # STEP 1 — SUPERSEDE OLDER DUPLICATE ITEMS
    # =========================================================
    superseded_item_ids: list[str] = []

    for item in older_duplicates:
        item.review_status = "REJECTED"
        item.updated_at = now

        supersede_note = (
            f"{DUPLICATE_SUPERSEDED_NOTE_PREFIX} "
            f"Superseded by newer unresolved duplicate item {survivor.id} "
            f"for normalized medication '{med_name_normalized}'."
        )

        _set_if_present(
            item,
            notes=_append_note(getattr(item, "notes", None), supersede_note),
        )

        superseded_item_ids.append(str(item.id))

    # =========================================================
    # STEP 2 — CLOSE OLDER ACTIVE TASKS LINKED TO THOSE ITEMS
    # =========================================================
    active_statuses = []
    for candidate in ("PENDING", "IN_PROGRESS", "OVERDUE"):
        if hasattr(TaskStatus, candidate):
            active_statuses.append(getattr(TaskStatus, candidate))

    closing_status = None
    for candidate in ("EXCUSED", "CANCELLED", "COMPLETED"):
        if hasattr(TaskStatus, candidate):
            closing_status = getattr(TaskStatus, candidate)
            break

    if closing_status is None:
        raise ValueError("No suitable task closing status found in TaskStatus enum")

    tasks_to_close = (
        db.query(Task)
        .filter(Task.reference_type == "MED_RECON_ITEM")
        .filter(Task.reference_id.in_(older_duplicate_ids))
        .filter(Task.status.in_(active_statuses))
        .order_by(Task.created_at.asc())
        .all()
    )

    closed_task_ids: list[str] = []

    for task in tasks_to_close:
        task.status = closing_status
        task.updated_at = now

        _set_if_present(
            task,
            completed_at=now,
            completion_reference_type="DOCUMENT",
            completion_reference_id=survivor.id,
            excused_reason_code="DUPLICATE_SUPERSEDED",
            excused_source="SYSTEM_DEDUP",
            excused_at=now,
            escalation_reason=(
                f"Older duplicate reconciliation task superseded by active duplicate item {survivor.id}"
            ),
            is_overdue=False,
        )

        closed_task_ids.append(str(task.id))

    logger.info(
        "MED_RECON_DEDUP: superseded_item_ids=%s closed_task_ids=%s survivor_item_id=%s",
        superseded_item_ids,
        closed_task_ids,
        str(survivor.id),
    )

    return {
        "kept_item_id": str(survivor.id),
        "superseded_item_ids": superseded_item_ids,
        "closed_task_ids": closed_task_ids,
    }