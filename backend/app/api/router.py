from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.domain.poc.poc_task_rules import POC_TO_TASK_MAP
from app.domain.tasks.task_escalation_routing import ESCALATION_ROUTING
from app.models.clinical_note import ClinicalNote
from app.models.enums import (
    TaskOrigin,
    TaskRegulatoryBasis,
    TaskStatus,
    TaskType,
)
from app.models.task import Task
from app.services.notification_engine import create_notification

logger = logging.getLogger("sns_emr")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# =========================================================
# ENUM SAFETY
# =========================================================

def _normalize(value: Any) -> str:
    return str(getattr(value, "value", value)).strip().upper() if value else ""


def _resolve_task_type(raw_value: Any, *, problem_code: str) -> TaskType:
    normalized = _normalize(raw_value)

    # direct enum match
    if hasattr(TaskType, normalized):
        return getattr(TaskType, normalized)

    # fallback mappings
    fallback_map = {
        "PAIN_MANAGEMENT": "CLINICAL_REVIEW_REQUIRED",
        "WOUND_MANAGEMENT": "CLINICAL_REVIEW_REQUIRED",
        "RESPIRATORY_MANAGEMENT": "CLINICAL_REVIEW_REQUIRED",
    }

    mapped = fallback_map.get(normalized)
    if mapped and hasattr(TaskType, mapped):
        logger.warning(
            "Remapped unsupported task type '%s' -> '%s'",
            normalized,
            mapped,
        )
        return getattr(TaskType, mapped)

    return getattr(TaskType, "OTHER")


def _pending_status():
    return getattr(TaskStatus, "PENDING", "PENDING")


def _system_origin():
    return getattr(TaskOrigin, "SYSTEM", "SYSTEM")


def _poc_regulatory_basis():
    return getattr(TaskRegulatoryBasis, "POC_UPDATE", "POC_UPDATE")


# =========================================================
# PRIORITY
# =========================================================

def _map_poc_severity_to_priority(poc: dict) -> str:
    severity = _normalize(poc.get("clinical_summary", {}).get("severity"))

    if severity in {"HIGH", "SEVERE", "CRITICAL"}:
        return "CRITICAL"
    if severity in {"MODERATE", "MEDIUM"}:
        return "HIGH"
    return "MEDIUM"


# =========================================================
# ESCALATION
# =========================================================

def _apply_escalation(priority: str) -> dict:
    now = _utcnow()

    if priority == "CRITICAL":
        return {"level": 1, "reason": "Immediate", "sla": now}
    if priority == "HIGH":
        return {"level": 1, "reason": "High", "sla": now + timedelta(hours=2)}

    return {"level": 1, "reason": "Routine", "sla": now + timedelta(hours=24)}


# =========================================================
# MAIN ENGINE
# =========================================================

def process_pocs_to_tasks(db: Session, *, note: ClinicalNote) -> None:
    if not note or not note.plan_of_care_updates:
        return

    pocs = note.plan_of_care_updates.get("pocs", [])
    if not pocs:
        return

    now = _utcnow()

    for poc in pocs:
        problem_code = _normalize(poc.get("problem", {}).get("code"))
        if not problem_code:
            continue

        rule = POC_TO_TASK_MAP.get(problem_code)
        if not rule:
            continue

        task_type = _resolve_task_type(rule.get("task_type"), problem_code=problem_code)

        # ✅ SMART DEDUPE (problem aware)
        existing = (
            db.query(Task)
            .filter(Task.patient_id == note.patient_id)
            .filter(Task.task_type == task_type)
            .filter(Task.alert_reason == f"POC_{problem_code}")
            .filter(Task.status.in_([_pending_status(), "IN_PROGRESS", "OVERDUE"]))
            .first()
        )

        if existing:
            continue

        priority = _map_poc_severity_to_priority(poc)
        escalation = _apply_escalation(priority)

        new_task = Task(
            id=uuid4(),
            tenant_id=note.tenant_id,
            patient_id=note.patient_id,
            task_type=task_type,
            status=_pending_status(),
            priority=priority,
            clinical_severity=poc.get("clinical_summary", {}).get("severity"),
            created_at=now,
            updated_at=now,
            due_date=escalation["sla"].date(),
            created_by=note.author_id,
            origin=_system_origin(),
            regulatory_basis=_poc_regulatory_basis(),
            reference_type="POC",
            reference_id=poc.get("poc_id"),
            clinical_note_id=note.id,
            alert_reason=f"POC_{problem_code}",
        )

        db.add(new_task)
        db.flush()

        logger.info(
            "Created POC task task_id=%s note_id=%s",
            str(new_task.id),
            str(note.id),
        )
