from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.domain.poc.poc_task_rules import POC_TO_TASK_MAP
from app.domain.tasks.task_escalation_routing import ESCALATION_ROUTING
from app.models.clinical_note import ClinicalNote
from app.models.enums import (
    TaskDiscipline,
    TaskOrigin,
    TaskRegulatoryBasis,
    TaskStatus,
    TaskType,
)
from app.models.task import Task
from app.services.notification_engine import create_notification

logger = logging.getLogger("sns_emr")


# =========================================================
# TIME HELPERS
# =========================================================

def _utcnow() -> datetime:
    """
    Return an aware UTC datetime for task timestamps.
    """
    return datetime.now(timezone.utc)


# =========================================================
# NORMALIZATION / ENUM HELPERS
# =========================================================

def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(getattr(value, "value", value)).strip().upper()


def _normalize_problem_code(value: Any) -> str:
    return _normalize_text(value)


def _enumish_text(value: Any) -> str:
    return str(getattr(value, "value", value)).strip()


def _resolve_task_type_member(raw_value: Any, *, problem_code: str) -> TaskType:
    """
    Resolve a supported TaskType enum member from a config/raw value.

    Prevents runtime failures from unsupported labels such as PAIN_MANAGEMENT.
    """
    normalized = _normalize_text(raw_value)

    # 1) direct member name
    if normalized and hasattr(TaskType, normalized):
        return getattr(TaskType, normalized)

    # 2) direct enum value
    for member in TaskType:
        if _normalize_text(member.value) == normalized:
            return member

    # 3) known legacy/custom aliases
    alias_map = {
        "PAIN_MANAGEMENT": "CLINICAL_REVIEW_REQUIRED",
        "WOUND_MANAGEMENT": "CLINICAL_REVIEW_REQUIRED",
        "RESPIRATORY_MANAGEMENT": "CLINICAL_REVIEW_REQUIRED",
        "PSYCHOSOCIAL_SUPPORT": "CLINICAL_FOLLOWUP",
        "SPIRITUAL_SUPPORT": "CLINICAL_FOLLOWUP",
    }

    alias_target = alias_map.get(normalized)
    if alias_target and hasattr(TaskType, alias_target):
        logger.warning(
            "Unsupported POC task label '%s' remapped to supported TaskType '%s'",
            normalized,
            alias_target,
        )
        return getattr(TaskType, alias_target)

    # 4) fallback by problem code
    if problem_code in {"PAIN", "WOUND", "RESPIRATORY"} and hasattr(
        TaskType, "CLINICAL_REVIEW_REQUIRED"
    ):
        logger.warning(
            "POC problem_code '%s' fell back to CLINICAL_REVIEW_REQUIRED",
            problem_code,
        )
        return TaskType.CLINICAL_REVIEW_REQUIRED

    if problem_code in {"PSYCHOSOCIAL", "SPIRITUAL"} and hasattr(
        TaskType, "CLINICAL_FOLLOWUP"
    ):
        logger.warning(
            "POC problem_code '%s' fell back to CLINICAL_FOLLOWUP",
            problem_code,
        )
        return TaskType.CLINICAL_FOLLOWUP

    if hasattr(TaskType, "OTHER"):
        logger.warning(
            "POC task label '%s' for problem_code '%s' fell back to OTHER",
            normalized,
            problem_code,
        )
        return TaskType.OTHER

    raise ValueError(
        f"Unable to resolve supported TaskType for raw_value={raw_value!r} "
        f"problem_code={problem_code!r}"
    )


def _resolve_status_member(*preferred_names: str):
    for name in preferred_names:
        member = getattr(TaskStatus, name, None)
        if member is not None:
            return member
    raise ValueError(
        f"TaskStatus missing required member from candidates: {preferred_names}"
    )


def _pending_status():
    return _resolve_status_member("PENDING", "OPEN", "DUE")


def _active_statuses() -> list:
    statuses = []
    for name in ("PENDING", "OPEN", "DUE", "IN_PROGRESS", "OVERDUE"):
        member = getattr(TaskStatus, name, None)
        if member is not None:
            statuses.append(member)

    if not statuses:
        raise ValueError("TaskStatus enum has no usable active statuses")

    return statuses


def _system_origin():
    for name in ("SYSTEM", "MANUAL"):
        member = getattr(TaskOrigin, name, None)
        if member is not None:
            return member
    raise ValueError("TaskOrigin enum has no usable SYSTEM or MANUAL member")


def _poc_regulatory_basis():
    member = getattr(TaskRegulatoryBasis, "POC_UPDATE", None)
    return member if member is not None else "POC_UPDATE"


def _resolve_discipline_member(raw_value: Any):
    """
    Resolve a TaskDiscipline member from POC intervention discipline.
    Falls back to RN for clinical POC review tasks.
    """
    normalized = _normalize_text(raw_value)

    if normalized and hasattr(TaskDiscipline, normalized):
        return getattr(TaskDiscipline, normalized)

    for member in TaskDiscipline:
        if _normalize_text(member.value) == normalized:
            return member

    fallback_map = {
        "SW": ("MSW",),
        "BSW": ("MSW",),
        "LCSW": ("MSW",),
        "CHAPLAIN": ("SC",),
    }

    for candidate in fallback_map.get(normalized, ()):
        if hasattr(TaskDiscipline, candidate):
            return getattr(TaskDiscipline, candidate)

    if hasattr(TaskDiscipline, "RN"):
        return getattr(TaskDiscipline, "RN")

    return "RN"


def _resolve_discipline_from_poc(poc: dict):
    """
    Pull the intended discipline from generated POC interventions.
    Falls back to RN when missing/invalid.
    """
    interventions = poc.get("interventions", [])
    if isinstance(interventions, list) and interventions:
        for entry in interventions:
            if isinstance(entry, dict):
                discipline = entry.get("discipline")
                if discipline:
                    return _resolve_discipline_member(discipline)

    return _resolve_discipline_member("RN")


# =========================================================
# PRIORITY MAPPING
# =========================================================

def _map_poc_severity_to_priority(poc: dict) -> str:
    """
    Map clinical severity to operational task priority.

    Supports values observed in current POC payloads:
    - SEVERE
    - HIGH
    - MODERATE
    - MILD
    - UNSPECIFIED
    """
    clinical_summary = poc.get("clinical_summary", {}) or {}
    severity = _normalize_text(clinical_summary.get("severity", "UNSPECIFIED"))

    if severity in {"SEVERE", "CRITICAL", "HIGH"}:
        return "CRITICAL"

    if severity in {"MODERATE", "MEDIUM"}:
        return "HIGH"

    if severity == "MILD":
        return "MEDIUM"

    return "MEDIUM"


# =========================================================
# ESCALATION RULES
# =========================================================

def _apply_escalation_rules(priority: str) -> dict:
    now = _utcnow()

    if priority == "CRITICAL":
        return {
            "level": 1,
            "reason": "Immediate escalation required",
            "sla_due_at": now,
        }

    if priority == "HIGH":
        return {
            "level": 1,
            "reason": "High priority condition",
            "sla_due_at": now + timedelta(hours=2),
        }

    if priority == "MEDIUM":
        return {
            "level": 1,
            "reason": "Routine monitoring",
            "sla_due_at": now + timedelta(hours=24),
        }

    return {
        "level": 0,
        "reason": None,
        "sla_due_at": now + timedelta(hours=24),
    }


# =========================================================
# ROUTING
# =========================================================

def _resolve_escalation_route(priority: str, level: int) -> dict:
    routing = ESCALATION_ROUTING.get(priority, {}) or {}
    return routing.get(level, {"role": None, "notify": False})


# =========================================================
# USER RESOLUTION
# =========================================================

def _resolve_assigned_user(
    db: Session,
    *,
    role: str,
    tenant_id=None,
):
    from app.models.user import User

    if not role:
        return None

    query = db.query(User).filter(User.role == role)

    if tenant_id is not None and hasattr(User, "tenant_id"):
        query = query.filter(User.tenant_id == tenant_id)

    if hasattr(User, "active"):
        query = query.filter(User.active.is_(True))

    user = query.order_by(getattr(User, "created_at", User.id)).first()
    return user.id if user else None


# =========================================================
# DEDUPE HELPERS
# =========================================================

def _poc_alert_reason(problem_code: str) -> str:
    return f"POC_{problem_code}"


def _find_existing_open_task_for_problem(
    db: Session,
    *,
    note: ClinicalNote,
    task_type: TaskType,
    problem_code: str,
):
    """
    Prevent duplicate open tasks for the same patient + problem code.

    This is more precise than deduping only on task_type because multiple
    problem codes can map to the same canonical task type.
    """
    query = (
        db.query(Task)
        .filter(Task.patient_id == note.patient_id)
        .filter(Task.task_type == task_type)
        .filter(Task.status.in_(_active_statuses()))
    )

    if hasattr(Task, "tenant_id"):
        query = query.filter(Task.tenant_id == note.tenant_id)

    if hasattr(Task, "alert_reason"):
        query = query.filter(Task.alert_reason == _poc_alert_reason(problem_code))

    return query.first()


# =========================================================
# MAIN ENGINE
# =========================================================

def process_pocs_to_tasks(
    db: Session,
    *,
    note: ClinicalNote,
) -> None:
    """
    Convert generated POCs into actionable tasks.

    Enterprise-safe behavior:
    - use only supported TaskType enum members
    - use canonical regulatory_basis = POC_UPDATE
    - link created tasks to the triggering clinical note
    - enforce required discipline on insert
    - dedupe by patient + problem code + canonical task type
    - annotate the POC JSON with task linkage
    - stay transaction-neutral (caller owns commit/rollback)
    """
    if not note or not note.plan_of_care_updates:
        return

    if not getattr(note, "patient_id", None) or not getattr(note, "tenant_id", None):
        return

    pocs = note.plan_of_care_updates.get("pocs", [])
    if not isinstance(pocs, list) or not pocs:
        return

    now = _utcnow()
    changed = False

    for poc in pocs:
        if not isinstance(poc, dict):
            continue

        # ---------------------------------------------
        # PROBLEM
        # ---------------------------------------------
        problem = poc.get("problem", {}) or {}
        problem_code = _normalize_problem_code(problem.get("code"))

        if not problem_code:
            continue

        # ---------------------------------------------
        # MAP → CANONICAL TASK TYPE
        # ---------------------------------------------
        rule = POC_TO_TASK_MAP.get(problem_code)
        if not rule:
            logger.info(
                "No POC_TO_TASK_MAP rule found for problem_code=%s note_id=%s",
                problem_code,
                str(getattr(note, "id", None)),
            )
            continue

        raw_task_type = rule.get("task_type")
        task_type = _resolve_task_type_member(
            raw_task_type,
            problem_code=problem_code,
        )

        # ---------------------------------------------
        # PREVENT DUPLICATE
        # ---------------------------------------------
        existing = _find_existing_open_task_for_problem(
            db,
            note=note,
            task_type=task_type,
            problem_code=problem_code,
        )

        if existing:
            poc["task_generated"] = True
            poc["task_id"] = str(getattr(existing, "id", None)) if getattr(existing, "id", None) else None
            if "task_history" not in poc or not isinstance(poc["task_history"], list):
                poc["task_history"] = []
            poc["task_history"].append(
                {
                    "event": "TASK_LINKED_EXISTING",
                    "task_id": str(getattr(existing, "id", None)) if getattr(existing, "id", None) else None,
                    "generated_at": now.isoformat(),
                }
            )
            changed = True
            logger.info(
                "Skipped duplicate POC task for patient_id=%s note_id=%s problem_code=%s task_type=%s existing_task_id=%s",
                str(getattr(note, "patient_id", None)),
                str(getattr(note, "id", None)),
                problem_code,
                _enumish_text(task_type),
                str(getattr(existing, "id", None)),
            )
            continue

        # ---------------------------------------------
        # PRIORITY + ESCALATION
        # ---------------------------------------------
        priority = _map_poc_severity_to_priority(poc)
        escalation = _apply_escalation_rules(priority)
        sla_due_at = escalation["sla_due_at"]
        due_date = sla_due_at.date() if sla_due_at else now.date()

        # ---------------------------------------------
        # ROUTING
        # ---------------------------------------------
        route = _resolve_escalation_route(priority, escalation["level"])

        assigned_role = route.get("role")
        notify_flag = bool(route.get("notify"))

        assigned_user_id = _resolve_assigned_user(
            db=db,
            role=assigned_role,
            tenant_id=note.tenant_id,
        )

        # ---------------------------------------------
        # DISCIPLINE (REQUIRED BY DB)
        # ---------------------------------------------
        discipline = _resolve_discipline_from_poc(poc)

        # ---------------------------------------------
        # CREATE TASK
        # ---------------------------------------------
        new_task = Task(
            id=uuid4(),
            tenant_id=note.tenant_id,
            patient_id=note.patient_id,
            task_type=task_type,
            status=_pending_status(),
            discipline=discipline,
            priority=priority,
            clinical_severity=poc.get("clinical_summary", {}).get("severity"),
            created_at=now,
            updated_at=now,
            due_date=due_date,
            created_by=getattr(note, "author_id", None),
            origin=_system_origin(),
            regulatory_basis=_poc_regulatory_basis(),
        )

        if hasattr(new_task, "due_at"):
            new_task.due_at = sla_due_at

        if hasattr(new_task, "sla_due_at"):
            new_task.sla_due_at = sla_due_at

        if hasattr(new_task, "escalation_level"):
            new_task.escalation_level = escalation["level"]

        if hasattr(new_task, "escalation_reason"):
            new_task.escalation_reason = escalation["reason"]

        if hasattr(new_task, "assigned_role"):
            new_task.assigned_role = assigned_role

        if hasattr(new_task, "assigned_user_id"):
            new_task.assigned_user_id = assigned_user_id

        if hasattr(new_task, "notification_required"):
            new_task.notification_required = notify_flag

        if hasattr(new_task, "reference_type"):
            new_task.reference_type = "POC"

        if hasattr(new_task, "reference_id"):
            new_task.reference_id = poc.get("poc_id")

        if hasattr(new_task, "clinical_note_id"):
            new_task.clinical_note_id = note.id

        if hasattr(new_task, "alert_reason"):
            new_task.alert_reason = _poc_alert_reason(problem_code)

        if hasattr(new_task, "details"):
            new_task.details = {
                "poc_problem_code": problem_code,
                "poc_problem_display": problem.get("display"),
                "poc_id": poc.get("poc_id"),
                "note_id": str(getattr(note, "id", None)) if getattr(note, "id", None) else None,
                "severity": poc.get("clinical_summary", {}).get("severity"),
                "discipline": _enumish_text(discipline),
            }

        if hasattr(new_task, "description"):
            display = problem.get("display") or problem_code.title()
            new_task.description = (
                f"Review generated {display} POC and associated clinical findings."
            )

        db.add(new_task)
        db.flush()

        poc["task_generated"] = True
        poc["task_id"] = str(getattr(new_task, "id", None)) if getattr(new_task, "id", None) else None
        if "task_history" not in poc or not isinstance(poc["task_history"], list):
            poc["task_history"] = []
        poc["task_history"].append(
            {
                "event": "TASK_GENERATED",
                "task_id": str(getattr(new_task, "id", None)) if getattr(new_task, "id", None) else None,
                "generated_at": now.isoformat(),
            }
        )
        changed = True

        logger.info(
            "Created POC task task_id=%s note_id=%s patient_id=%s task_type=%s problem_code=%s discipline=%s",
            str(getattr(new_task, "id", None)),
            str(getattr(note, "id", None)),
            str(getattr(note, "patient_id", None)),
            _enumish_text(task_type),
            problem_code,
            _enumish_text(discipline),
        )

        # ---------------------------------------------
        # NOTIFICATION
        # ---------------------------------------------
        if notify_flag and assigned_user_id:
            create_notification(
                db=db,
                tenant_id=note.tenant_id,
                user_id=assigned_user_id,
                patient_id=note.patient_id,
                title=f"New Task: {_enumish_text(task_type)}",
                message=(
                    f"You have been assigned a {priority} priority task "
                    f"for POC problem {problem_code}."
                ),
                notification_type="TASK_ASSIGNED",
                source_type="TASK",
                source_id=new_task.id,
            )

    if changed:
        flag_modified(note, "plan_of_care_updates")
        db.add(note)