# app/services/poc_warning_tasks.py

from __future__ import annotations

import logging
from datetime import datetime, timezone, date, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.benefit_period import BenefitPeriod
from app.models.enums import TaskStatus, TaskDiscipline, TaskType


logger = logging.getLogger("sns_emr")


WARN_DISCIPLINES = ["RN", "NP", "MD"]


# =========================================================
# HELPERS
# =========================================================

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _task_type(value):
    """
    Safe resolver for task_type.
    """
    if hasattr(TaskType, value):
        return getattr(TaskType, value)
    return value


def _completed_status():
    member = getattr(TaskStatus, "COMPLETED", None)
    return member if member is not None else "COMPLETED"


def _overdue_status():
    member = getattr(TaskStatus, "OVERDUE", None)
    return member if member is not None else None


def _inactive_statuses():
    statuses = []
    for name in ("COMPLETED", "CANCELLED", "DISMISSED", "CLOSED"):
        member = getattr(TaskStatus, name, None)
        if member is not None:
            statuses.append(member)
    return statuses


def _resolve_discipline(value):
    normalized = str(value).upper()
    if hasattr(TaskDiscipline, normalized):
        return getattr(TaskDiscipline, normalized)

    fallback = getattr(TaskDiscipline, "RN", None)
    return fallback if fallback is not None else normalized


def _normalize_status(value) -> str:
    if value is None:
        return ""
    return str(getattr(value, "value", value)).strip().upper()


# =========================================================
# BENEFIT PERIOD
# =========================================================

def _get_current_benefit_period_id(db: Session, patient_id):
    """
    Picks the active benefit period for the patient.
    """
    today = datetime.utcnow().date()

    query = db.query(BenefitPeriod).filter(
        BenefitPeriod.patient_id == patient_id
    )

    if hasattr(BenefitPeriod, "start_date") and hasattr(BenefitPeriod, "end_date"):
        query = (
            query
            .filter(BenefitPeriod.start_date <= today)
            .filter(
                (BenefitPeriod.end_date == None) |
                (BenefitPeriod.end_date >= today)
            )
        )
        bp = query.order_by(BenefitPeriod.start_date.desc()).first()
    else:
        bp = query.order_by(BenefitPeriod.created_at.desc()).first()

    if not bp:
        raise ValueError(
            "No active benefit period found for patient. Cannot create POC warning tasks."
        )

    return bp.id


# =========================================================
# TASK DEDUPE
# =========================================================

def _has_open_task(
    db: Session,
    *,
    patient_id,
    benefit_period_id,
    task_type,
    discipline,
    tenant_id=None,
):
    query = (
        db.query(Task)
        .filter(Task.patient_id == patient_id)
        .filter(Task.benefit_period_id == benefit_period_id)
        .filter(Task.task_type == task_type)
        .filter(Task.discipline == discipline)
    )

    if tenant_id is not None and hasattr(Task, "tenant_id"):
        query = query.filter(Task.tenant_id == tenant_id)

    inactive = _inactive_statuses()

    if inactive:
        query = query.filter(~Task.status.in_(inactive))
    else:
        query = query.filter(Task.status != _completed_status())

    return db.query(query.exists()).scalar()


# =========================================================
# ESCALATION HELPERS
# =========================================================

def _warning_priority_for_level(level: int) -> str:
    """
    Recommended operational priority map for overdue warning tasks.

    This is an engineering policy choice, not directly prescribed by regulation.
    """
    if level >= 3:
        return "CRITICAL"
    if level == 2:
        return "HIGH"
    return "MEDIUM"


def _escalation_reason(level: int) -> str:
    if level >= 3:
        return "POC warning task remains overdue after repeated escalation."
    if level == 2:
        return "POC warning task remains overdue after first escalation."
    return "POC warning task is overdue."


def _next_escalation_level(task) -> int:
    current = getattr(task, "escalation_level", None)
    if current is None:
        return 1

    try:
        return int(current) + 1
    except Exception:
        return 1


def _append_escalation_history(task, *, level: int, reason: str, now: datetime) -> None:
    if not hasattr(task, "details"):
        return

    existing_details = getattr(task, "details", None)
    if not isinstance(existing_details, dict):
        task.details = {}

    if "escalation_history" not in task.details or not isinstance(task.details["escalation_history"], list):
        task.details["escalation_history"] = []

    task.details["escalation_history"].append(
        {
            "level": level,
            "reason": reason,
            "timestamp": now.isoformat(),
        }
    )


# =========================================================
# MAIN WARNING CREATION FUNCTION
# =========================================================

def warn_rn_np_md(
    *,
    db: Session,
    patient_id,
    task_type: str,
    due_date: date,
    origin: str,
    message: str,
    reference_type=None,
    reference_id=None,
    tenant_id: Optional[UUID] = None,
    actor_user_id: Optional[UUID] = None,
) -> int:
    """
    Creates up to 3 tasks: RN, NP, MD.

    Behavior:
    - Uses benefit_period_id (required)
    - Dedupes existing open tasks
    - Adds audit metadata
    - Logs activity
    """

    if db is None:
        logger.error("warn_rn_np_md called with db=None")
        return 0

    if not patient_id:
        logger.warning("warn_rn_np_md called without patient_id")
        return 0

    now = _utcnow()
    created = 0

    benefit_period_id = _get_current_benefit_period_id(db, patient_id)
    resolved_task_type = _task_type(task_type)

    for discipline_raw in WARN_DISCIPLINES:

        discipline = _resolve_discipline(discipline_raw)

        if _has_open_task(
            db,
            patient_id=patient_id,
            benefit_period_id=benefit_period_id,
            task_type=resolved_task_type,
            discipline=discipline,
            tenant_id=tenant_id,
        ):
            continue

        task = Task(
            patient_id=patient_id,
            benefit_period_id=benefit_period_id,
            discipline=discipline,
            task_type=resolved_task_type,
            origin=origin,
            regulatory_basis="POC_UPDATE",
            status="PENDING",
            due_date=due_date,
            completion_reference_type=reference_type,
            completion_reference_id=str(reference_id) if reference_id else None,
        )

        # Optional fields (safe)
        if hasattr(task, "tenant_id"):
            task.tenant_id = tenant_id

        if hasattr(task, "created_at"):
            task.created_at = now

        if hasattr(task, "updated_at"):
            task.updated_at = now

        if hasattr(task, "created_by"):
            task.created_by = actor_user_id

        if hasattr(task, "priority"):
            task.priority = "MEDIUM"

        if hasattr(task, "escalation_level"):
            task.escalation_level = 0

        if hasattr(task, "escalation_reason"):
            task.escalation_reason = None

        if hasattr(task, "is_overdue"):
            task.is_overdue = False

        if hasattr(task, "sla_due_at"):
            task.sla_due_at = datetime.combine(due_date, datetime.min.time(), tzinfo=timezone.utc)

        if hasattr(task, "details"):
            task.details = {
                "type": "POC_WARNING",
                "discipline": discipline_raw,
                "message": message,
                "generated_at": now.isoformat(),
                "escalation_history": [],
            }

        db.add(task)
        created += 1

    logger.info(
        "POC warning tasks created=%s patient_id=%s task_type=%s",
        created,
        str(patient_id),
        str(task_type),
    )

    return created


# =========================================================
# OVERDUE ESCALATION
# =========================================================

def escalate_overdue_poc_warning_tasks(
    *,
    db: Session,
    tenant_id: Optional[UUID] = None,
    as_of_date: Optional[date] = None,
    actor_user_id: Optional[UUID] = None,
    task_type: str = "POC_NONCOMPLIANT_STRUCTURE",
) -> int:
    """
    Escalate overdue POC warning tasks.

    Recommended behavior:
    - only unresolved tasks
    - only tasks with due_date before the as_of_date
    - increment escalation level
    - mark overdue flag if available
    - set OVERDUE status if supported by the enum
    - update priority / reason if those fields exist

    IMPORTANT:
    - This does NOT auto-complete tasks
    - This does NOT attach correction evidence
    """

    if db is None:
        logger.error("escalate_overdue_poc_warning_tasks called with db=None")
        return 0

    today = as_of_date or _utcnow().date()
    now = _utcnow()

    resolved_task_type = _task_type(task_type)

    query = db.query(Task).filter(Task.task_type == resolved_task_type)

    if tenant_id is not None and hasattr(Task, "tenant_id"):
        query = query.filter(Task.tenant_id == tenant_id)

    if hasattr(Task, "due_date"):
        query = query.filter(Task.due_date < today)
    else:
        logger.warning("Task model has no due_date field; overdue escalation skipped")
        return 0

    inactive = _inactive_statuses()
    if inactive:
        query = query.filter(~Task.status.in_(inactive))
    else:
        query = query.filter(Task.status != _completed_status())

    tasks = query.all()

    escalated = 0
    overdue_member = _overdue_status()

    for task in tasks:
        current_status = _normalize_status(getattr(task, "status", None))
        if current_status in {"COMPLETED", "CANCELLED", "DISMISSED", "CLOSED"}:
            continue

        level = _next_escalation_level(task)
        reason = _escalation_reason(level)
        priority = _warning_priority_for_level(level)

        if overdue_member is not None:
            task.status = overdue_member

        if hasattr(task, "is_overdue"):
            task.is_overdue = True

        if hasattr(task, "priority"):
            task.priority = priority

        if hasattr(task, "escalation_level"):
            task.escalation_level = level

        if hasattr(task, "escalation_reason"):
            task.escalation_reason = reason

        if hasattr(task, "updated_at"):
            task.updated_at = now

        if hasattr(task, "updated_by"):
            task.updated_by = actor_user_id

        _append_escalation_history(
            task,
            level=level,
            reason=reason,
            now=now,
        )

        escalated += 1

    logger.info(
        "Escalated overdue POC warning tasks count=%s task_type=%s as_of_date=%s",
        escalated,
        str(task_type),
        str(today),
    )

    return escalated