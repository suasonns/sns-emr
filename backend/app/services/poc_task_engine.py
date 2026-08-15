# backend/app/services/poc_task_engine.py

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.domain.poc.poc_task_rules import POC_TO_TASK_MAP
from app.domain.tasks.task_escalation_routing import ESCALATION_ROUTING
from app.models.enums import TaskType, TaskStatus, TaskOrigin, TaskRegulatoryBasis
from app.models.task import Task


# =========================================================
# HELPERS
# =========================================================

def _utcnow():
    return datetime.now(timezone.utc)


def _normalize_text(value):
    if value is None:
        return ""
    return str(getattr(value, "value", value)).strip().upper()


def _resolve_task_type_member(raw_value, *, problem_code):
    normalized = _normalize_text(raw_value)

    if normalized and hasattr(TaskType, normalized):
        return getattr(TaskType, normalized)

    for member in TaskType:
        if _normalize_text(member.value) == normalized:
            return member

    fallback = getattr(TaskType, "CLINICAL_REVIEW_REQUIRED", None)
    if fallback:
        return fallback

    raise ValueError("Cannot resolve TaskType")


def _pending_status():
    return getattr(TaskStatus, "PENDING", TaskStatus.OPEN)


def _system_origin():
    return getattr(TaskOrigin, "SYSTEM", TaskOrigin.MANUAL)


def _poc_regulatory_basis():
    return getattr(TaskRegulatoryBasis, "POC_UPDATE", "POC_UPDATE")


def _map_priority(poc):
    severity = _normalize_text(
        (poc.get("clinical_summary") or {}).get("severity")
    )

    if severity in {"CRITICAL", "SEVERE", "HIGH"}:
        return "CRITICAL"
    if severity in {"MODERATE", "MEDIUM"}:
        return "HIGH"

    return "MEDIUM"


def _apply_escalation(priority):
    now = _utcnow()

    if priority == "CRITICAL":
        return now
    if priority == "HIGH":
        return now + timedelta(hours=2)

    return now + timedelta(hours=24)


def _find_existing_task(db, *, patient_id, tenant_id, task_type, problem_code):
    query = (
        db.query(Task)
        .filter(Task.patient_id == patient_id)
        .filter(Task.task_type == task_type)
        .filter(Task.alert_reason == f"POC_{problem_code}")
    )

    if hasattr(Task, "tenant_id"):
        query = query.filter(Task.tenant_id == tenant_id)

    return query.first()


# =========================================================
# MAIN ENGINE
# =========================================================

def process_poc_version_to_tasks(
    db: Session,
    *,
    poc_version
):
    """
    ✅ Correct production version
    - Reads from snapshot_json
    - NO mutation of POC JSON
    - Inserts tasks into DB
    """

    if not poc_version:
        return

    poc_data = poc_version.snapshot_json or {}

    # Legacy draft-generator shape
    if isinstance(poc_data.get("pocs"), list):
        pocs = poc_data["pocs"]

    # Canonical compiler shape
    elif isinstance(poc_data.get("problems"), list):
        pocs = [
            {
                "poc_id": problem.get("problem_code"),
                "problem": {
                    "code": problem.get("problem_code"),
                    "label": problem.get("label"),
                },
                "clinical_summary": {
                    "severity": problem.get("severity"),
                },
            }
            for problem in poc_data["problems"]
        ]

    else:
        return

    if not pocs:
        return

    now = _utcnow()

    patient_id = poc_version.plan_of_care.patient_id
    tenant_id = poc_version.plan_of_care.tenant_id

    for poc in pocs:
        if not isinstance(poc, dict):
            continue

        problem = poc.get("problem") or {}
        problem_code = _normalize_text(problem.get("code"))

        if not problem_code:
            continue

        rule = POC_TO_TASK_MAP.get(problem_code)
        if not rule:
            continue

        task_type = _resolve_task_type_member(
            rule.get("task_type"),
            problem_code=problem_code
        )

        # ✅ DEDUPE
        existing = _find_existing_task(
            db,
            patient_id=patient_id,
            tenant_id=tenant_id,
            task_type=task_type,
            problem_code=problem_code
        )

        if existing:
            continue

        priority = _map_priority(poc)
        sla_due_at = _apply_escalation(priority)

        # ✅ CREATE TASK
        new_task = Task(
            id=uuid4(),
            tenant_id=tenant_id,
            patient_id=patient_id,
            task_type=task_type,
            status=_pending_status(),
            priority=priority,
            created_at=now,
            updated_at=now,
            due_date=sla_due_at.date(),
            due_at=sla_due_at,
            origin=_system_origin(),
            regulatory_basis=_poc_regulatory_basis(),
            reference_type="POC",
            reference_id=poc.get("poc_id"),
            alert_reason=f"POC_{problem_code}",
        )

        db.add(new_task)

    # ✅ CRITICAL: force insert into DB (before commit)
    db.flush()