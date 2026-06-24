# backend/app/services/task_sla_engine.py

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.enums import TaskDiscipline, CompletionReferenceType
from app.models.visit import Visit


# =========================================================
# SLA CONFIGURATION (ENTERPRISE POLICY LAYER)
# =========================================================

SLA_CONFIG = {
    "CLINICAL": timedelta(hours=24),
    "PSYCHOSOCIAL": timedelta(hours=48),
    "SPIRITUAL": timedelta(hours=72),
}


# =========================================================
# TIME HELPERS
# =========================================================

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


# =========================================================
# DOMAIN RESOLUTION
# =========================================================

def _resolve_domain_from_discipline(task: Task) -> str:
    """
    Resolve SLA domain using discipline.

    Deterministic + fallback safe.
    """

    if task.discipline in (
        TaskDiscipline.SW,
        TaskDiscipline.MSW,
        TaskDiscipline.BSW,
        TaskDiscipline.LCSW,
    ):
        return "PSYCHOSOCIAL"

    if task.discipline == TaskDiscipline.SC:
        return "SPIRITUAL"

    return "CLINICAL"


# =========================================================
# SLA ANCHOR RESOLUTION (CRITICAL FIX)
# =========================================================

def _resolve_sla_start(
    db: Session,
    *,
    task: Task,
) -> datetime:
    """
    Determine SLA start timestamp.

    Priority:
    1. VISIT anchor → visit.visit_datetime
    2. fallback → now()
    """

    if getattr(task, "completion_reference_type", None) == CompletionReferenceType.VISIT:
        visit_id = getattr(task, "completion_reference_id", None)

        if visit_id:
            visit = (
                db.query(Visit)
                .filter(Visit.id == visit_id)
                .first()
            )

            if visit and getattr(visit, "visit_datetime", None):
                return visit.visit_datetime

    return _now_utc()


# =========================================================
# MAIN SLA ENGINE
# =========================================================

def assign_sla_to_task(
    db: Session,
    *,
    task: Task,
) -> Task:
    """
    Assign SLA timestamps to a task.

    ENTERPRISE BEHAVIOR:
    - Idempotent (does not override existing SLA)
    - Skips completed tasks
    - Anchors SLA to clinical event when possible
    - Does NOT commit
    """

    # ✅ Skip completed tasks
    try:
        if task.status.name == "COMPLETED":
            return task
    except Exception:
        pass

    existing_start = getattr(task, "sla_start_at", None)
    existing_due = getattr(task, "sla_due_at", None)

    if existing_start and existing_due:
        return task

    # ✅ Resolve SLA domain
    domain = _resolve_domain_from_discipline(task)
    sla_duration = SLA_CONFIG.get(domain, SLA_CONFIG["CLINICAL"])

    # ✅ Resolve correct anchor
    start = existing_start or _resolve_sla_start(db=db, task=task)

    # ✅ Assign values
    if hasattr(task, "sla_start_at") and not existing_start:
        task.sla_start_at = start

    if hasattr(task, "sla_due_at") and not existing_due:
        task.sla_due_at = start + sla_duration

    # ✅ Reset overdue state (optional safety)
    if hasattr(task, "is_overdue") and task.is_overdue:
        task.is_overdue = False

    db.add(task)
    db.flush()

    return task


# =========================================================
# BULK SLA ENGINE
# =========================================================

def assign_sla_to_tasks_bulk(
    db: Session,
    *,
    tasks: List[Task],
) -> None:
    """
    Bulk SLA assignment.

    Safe, idempotent batch operation.
    """

    for task in tasks:
        assign_sla_to_task(
            db=db,
            task=task,
        )

    db.flush()