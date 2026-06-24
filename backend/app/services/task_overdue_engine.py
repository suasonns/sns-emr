from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import UUID

from sqlalchemy import func, or_, and_
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.enums import TaskStatus


# =========================================================
# SYSTEM DEFAULTS
# =========================================================

SYSTEM_ENGINE_ROLE = "SYSTEM_ENGINE"


# =========================================================
# TIME HELPERS
# =========================================================

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


# =========================================================
# ENUM HELPERS
# =========================================================

def _resolve_status_optional(*candidates: str):
    """
    Resolve TaskStatus by enum member name or enum value.
    Returns None if no match is found.
    """
    for candidate in candidates:
        if candidate in TaskStatus.__members__:
            return TaskStatus.__members__[candidate]

        for member in TaskStatus:
            if str(member.value) == candidate:
                return member

    return None


def _resolve_status_required(*candidates: str):
    """
    Resolve TaskStatus by enum member name or enum value.
    Raises if no match is found.
    """
    value = _resolve_status_optional(*candidates)
    if value is None:
        raise ValueError(f"Could not resolve TaskStatus from {candidates}")
    return value


def _completed_status():
    return _resolve_status_required("COMPLETED")


def _pending_status():
    return _resolve_status_required("PENDING")


def _due_status_optional():
    return _resolve_status_optional("PENDING")


def _overdue_status_optional():
    return _resolve_status_optional("OVERDUE")


def _escalated_status_optional():
    return _resolve_status_optional("ESCALATED")


def _waived_status_optional():
    return _resolve_status_optional("WAIVED")


def _pending_like_statuses():
    """
    Statuses eligible to become overdue.
    """
    values = [_pending_status()]

    due = _due_status_optional()
    if due is not None and due not in values:
        values.append(due)

    return values


def _actionable_statuses():
    """
    Statuses visible in RN dashboards / work queues.
    """
    values = list(_pending_like_statuses())

    overdue = _overdue_status_optional()
    if overdue is not None and overdue not in values:
        values.append(overdue)

    escalated = _escalated_status_optional()
    if escalated is not None and escalated not in values:
        values.append(escalated)

    return values


def _preferred_overdue_status():
    """
    Preferred overdue state transition:
    - OVERDUE if available
    - else ESCALATED if available
    - else raise
    """
    overdue = _overdue_status_optional()
    if overdue is not None:
        return overdue

    escalated = _escalated_status_optional()
    if escalated is not None:
        return escalated

    raise ValueError("Neither OVERDUE nor ESCALATED exists in TaskStatus enum")


# =========================================================
# DUE FIELD HELPERS
# =========================================================

def _has_sla_due_at() -> bool:
    return hasattr(Task, "sla_due_at")


def _has_due_date() -> bool:
    return hasattr(Task, "due_date")


def _has_due_signal() -> bool:
    return _has_sla_due_at() or _has_due_date()


# =========================================================
# READ MODEL
# =========================================================

def evaluate_task_timeliness(
    *,
    db: Session,
    tenant_id: UUID,
    as_of: Optional[datetime] = None,
) -> Dict[str, int]:
    """
    Enterprise read model for SLA dashboards and compliance reports.

    Returns:
    - open_tasks
    - overdue_tasks
    - completed_tasks
    - missing_sla_tasks

    Safe behavior:
    - If no due signal exists on the ORM model, overdue-related metrics return zero.
    - Supports either:
        - Task.sla_due_at (datetime)
        - Task.due_date (date)
    - If both exist:
        - uses sla_due_at when populated
        - falls back to due_date when sla_due_at is NULL
    """

    now = as_of or _now_utc()
    today = now.date()

    completed_status = _completed_status()
    actionable_statuses = _actionable_statuses()

    open_tasks = (
        db.query(func.count(Task.id))
        .filter(
            Task.tenant_id == tenant_id,
            Task.status.in_(actionable_statuses),
        )
        .scalar()
        or 0
    )

    if _has_sla_due_at() and _has_due_date():
        overdue_tasks = (
            db.query(func.count(Task.id))
            .filter(
                Task.tenant_id == tenant_id,
                Task.status.in_(actionable_statuses),
                or_(
                    and_(
                        Task.sla_due_at.isnot(None),
                        Task.sla_due_at < now,
                    ),
                    and_(
                        Task.sla_due_at.is_(None),
                        Task.due_date.isnot(None),
                        Task.due_date < today,
                    ),
                ),
            )
            .scalar()
            or 0
        )

        missing_sla_tasks = (
            db.query(func.count(Task.id))
            .filter(
                Task.tenant_id == tenant_id,
                Task.status.in_(actionable_statuses),
                Task.sla_due_at.is_(None),
                Task.due_date.is_(None),
            )
            .scalar()
            or 0
        )

    elif _has_sla_due_at():
        overdue_tasks = (
            db.query(func.count(Task.id))
            .filter(
                Task.tenant_id == tenant_id,
                Task.status.in_(actionable_statuses),
                Task.sla_due_at.isnot(None),
                Task.sla_due_at < now,
            )
            .scalar()
            or 0
        )

        missing_sla_tasks = (
            db.query(func.count(Task.id))
            .filter(
                Task.tenant_id == tenant_id,
                Task.status.in_(actionable_statuses),
                Task.sla_due_at.is_(None),
            )
            .scalar()
            or 0
        )

    elif _has_due_date():
        overdue_tasks = (
            db.query(func.count(Task.id))
            .filter(
                Task.tenant_id == tenant_id,
                Task.status.in_(actionable_statuses),
                Task.due_date.isnot(None),
                Task.due_date < today,
            )
            .scalar()
            or 0
        )

        missing_sla_tasks = (
            db.query(func.count(Task.id))
            .filter(
                Task.tenant_id == tenant_id,
                Task.status.in_(actionable_statuses),
                Task.due_date.is_(None),
            )
            .scalar()
            or 0
        )

    else:
        overdue_tasks = 0
        missing_sla_tasks = 0

    completed_tasks = (
        db.query(func.count(Task.id))
        .filter(
            Task.tenant_id == tenant_id,
            Task.status == completed_status,
        )
        .scalar()
        or 0
    )

    return {
        "open_tasks": int(open_tasks),
        "overdue_tasks": int(overdue_tasks),
        "completed_tasks": int(completed_tasks),
        "missing_sla_tasks": int(missing_sla_tasks),
    }


# =========================================================
# MAIN ENGINE
# =========================================================

def run_overdue_engine(
    *,
    db: Session,
    tenant_id: UUID,
    actor_user_id: Optional[UUID] = None,
    actor_role: Optional[str] = None,
    as_of: Optional[datetime] = None,
) -> int:
    """
    SLA / due-date overdue detection engine.

    ENTERPRISE BEHAVIOR:
    - Finds pending-like tasks whose due signal has passed.
    - Supports either:
        - Task.sla_due_at (datetime)
        - Task.due_date (date)
    - If both exist:
        - due_date is treated as an independent overdue signal
        - sla_due_at is also treated as an independent overdue signal
    - Skips completed / waived tasks.
    - Marks is_overdue = True if field exists.
    - Sets escalation_level to at least 1 on first overdue detection if field exists.
    - Sets escalated_at on first overdue detection if field exists.
    - Sets escalation_reason on first overdue detection if field exists.
    - Sets status to OVERDUE if available, else ESCALATED.
    - Does NOT commit. Caller owns transaction boundary.

    Returns:
        number of tasks updated
    """

    if not _has_due_signal():
        return 0

    now = as_of or _now_utc()
    today = now.date()

    pending_like = _pending_like_statuses()

    query = db.query(Task).filter(
        Task.tenant_id == tenant_id,
        Task.status.in_(pending_like),
    )

    if _has_sla_due_at() and _has_due_date():
        query = query.filter(
            or_(
                and_(
                    Task.due_date.isnot(None),
                    Task.due_date < today,
                ),
                and_(
                    Task.sla_due_at.isnot(None),
                    Task.sla_due_at < now,
                ),
            )
        )
    elif _has_sla_due_at():
        query = query.filter(
            Task.sla_due_at.isnot(None),
            Task.sla_due_at < now,
        )
    elif _has_due_date():
        query = query.filter(
            Task.due_date.isnot(None),
            Task.due_date < today,
        )

    tasks = query.all()

    updated_count = 0

    for task in tasks:
        changed = _mark_task_overdue(
            task=task,
            now=now,
            actor_user_id=actor_user_id,
            actor_role=actor_role or SYSTEM_ENGINE_ROLE,
        )
        if changed:
            db.add(task)
            updated_count += 1

    if updated_count:
        db.flush()

    return updated_count

# =========================================================
# TASK PROCESSOR
# =========================================================

def _mark_task_overdue(
    *,
    task: Task,
    now: datetime,
    actor_user_id: Optional[UUID],
    actor_role: str,
) -> bool:
    """
    Mark a single task overdue.

    Idempotency:
    - If task is already overdue/escalated, no repeated mutation occurs.
    - escalation_level is not repeatedly incremented.
    - existing escalation_reason is preserved.

    Returns:
        True if task was changed
        False if no mutation was necessary
    """

    completed_status = _completed_status()
    waived_status = _waived_status_optional()

    if task.status == completed_status:
        return False

    if waived_status is not None and task.status == waived_status:
        return False

    target_status = _preferred_overdue_status()

    status_changed = task.status != target_status
    was_overdue = bool(getattr(task, "is_overdue", False))
    any_change = False

    if hasattr(task, "is_overdue") and not was_overdue:
        task.is_overdue = True
        any_change = True

    if status_changed:
        task.status = target_status
        any_change = True

    if not was_overdue:
        if hasattr(task, "escalation_level"):
            current_level = getattr(task, "escalation_level", 0) or 0
            new_level = max(current_level, 1)
            if new_level != current_level:
                task.escalation_level = new_level
                any_change = True

        if hasattr(task, "escalated_at") and getattr(task, "escalated_at", None) is None:
            task.escalated_at = now
            any_change = True

        if hasattr(task, "escalation_reason"):
            existing_reason = getattr(task, "escalation_reason", None)
            if not existing_reason:
                task.escalation_reason = "Task exceeded due deadline without completion."
                any_change = True

    if hasattr(task, "updated_at") and any_change:
        task.updated_at = now

    return any_change
