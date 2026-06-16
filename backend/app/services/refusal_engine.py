from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.enums import TaskStatus, TaskType
from app.models.patient import Patient
from app.models.refusal import Refusal
from app.models.task import Task


# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger(__name__)


# =========================================================
# DISCIPLINE RULES
# =========================================================

REFUSABLE_DISCIPLINES = {
    "LVN",
    "AIDE",
    "CHHA",
    "HHA",
    "SW",
    "MSW",
    "LCSW",
    "CHAPLAIN",
    "SC",
}

NON_REFUSABLE_DISCIPLINES = {
    "RN",
    "MD",
    "F2F",
}

# ✅ FINAL CANONICAL SET (HARDENED)
VALID_REFUSAL_DISCIPLINES = {
    "RN",
    "MD",
    "F2F",
    "SW",
    "CHAPLAIN",
    "AIDE",
}


# =========================================================
# NORMALIZATION
# =========================================================

def normalize_refusal_discipline(value: str) -> str:
    discipline = (value or "").strip().upper()

    if discipline in {"MSW", "LCSW", "SW"}:
        return "SW"
    if discipline in {"SC", "CHAPLAIN"}:
        return "CHAPLAIN"
    if discipline in {"HHA", "CHHA", "AIDE"}:
        return "AIDE"

    return discipline


def _reoffer_task_type_for_discipline(discipline: str) -> Optional[TaskType]:
    if discipline == "SW":
        return TaskType.MSW_REOFFER
    if discipline == "CHAPLAIN":
        return TaskType.CHAPLAIN_REOFFER
    if discipline == "AIDE":
        return TaskType.AIDE_REOFFER
    return None


# =========================================================
# TASK HELPERS
# =========================================================

def _create_task_if_missing(
    db: Session,
    *,
    patient: Patient,
    user_id,
    now: datetime,
    task_type: TaskType,
    task_status: TaskStatus,
    alert_reason: str,
    discipline: Optional[str] = None,
) -> bool:

    query = (
        db.query(Task)
        .execution_options(skip_tenant_filter=True)
        .filter(
            Task.tenant_id == patient.tenant_id,
            Task.patient_id == patient.id,
            Task.task_type == task_type,
            Task.status == TaskStatus.PENDING,
        )
    )

    if discipline and hasattr(Task, "discipline"):
        query = query.filter(Task.discipline == discipline)

    if hasattr(Task, "alert_reason"):
        query = query.filter(Task.alert_reason == alert_reason)

    existing = query.first()

    if existing:
        return False

    task = Task(
        id=uuid.uuid4(),
        tenant_id=patient.tenant_id,
        patient_id=patient.id,
        task_type=task_type,
        status=task_status,
        created_at=now,
        created_by=user_id,
    )

    if hasattr(task, "updated_at"):
        task.updated_at = now

    if hasattr(task, "due_date"):
        task.due_date = now.date()

    if hasattr(task, "origin"):
        task.origin = "SYSTEM"

    if hasattr(task, "discipline") and discipline:
        task.discipline = discipline

    if hasattr(task, "regulatory_basis"):
        task.regulatory_basis = "CONDITION_TRIGGER"

    if hasattr(task, "alert_reason"):
        task.alert_reason = alert_reason

    db.add(task)
    return True


# =========================================================
# PUBLIC SERVICE API
# =========================================================

def record_refusal(
    db: Session,
    *,
    patient: Patient,
    user_id,
    discipline: str,
    reason: Optional[str] = None,
) -> Refusal:

    now = datetime.now(timezone.utc)

    # ✅ STEP 1: normalize input
    canonical_discipline = normalize_refusal_discipline(discipline)

    # ✅ STEP 2: DEFENSIVE LOGGING + VALIDATION
    if canonical_discipline not in VALID_REFUSAL_DISCIPLINES:
        logger.error(
            "INVALID_DISCIPLINE_AFTER_NORMALIZATION",
            extra={
                "input_discipline": discipline,
                "canonical_discipline": canonical_discipline,
                "patient_id": str(patient.id),
            },
        )
        raise ValueError(
            f"Invalid discipline after normalization: {canonical_discipline}"
        )

    # ✅ STEP 3: create refusal record
    refusal = Refusal(
        id=uuid.uuid4(),
        tenant_id=patient.tenant_id,
        patient_id=patient.id,
        discipline=canonical_discipline,
        reason=reason,
        refused_at=now,
        was_reoffered=False,
        reoffered_at=None,
        created_by=user_id,
        updated_at=now,
    )
    db.add(refusal)

    # -----------------------------------------------------
    # REFUSABLE → RE-OFFER TASK
    # -----------------------------------------------------
    if canonical_discipline in {"SW", "CHAPLAIN", "AIDE", "LVN"}:
        task_type = _reoffer_task_type_for_discipline(canonical_discipline)

        if task_type is not None:
            _create_task_if_missing(
                db=db,
                patient=patient,
                user_id=user_id,
                now=now,
                task_type=task_type,
                task_status=TaskStatus.PENDING,
                alert_reason=f"{canonical_discipline}_VISIT_REFUSED_FOLLOWUP_REQUIRED",
                discipline=canonical_discipline,
            )
        else:
            _create_task_if_missing(
                db=db,
                patient=patient,
                user_id=user_id,
                now=now,
                task_type=TaskType.OTHER,
                task_status=TaskStatus.PENDING,
                alert_reason=f"{canonical_discipline}_VISIT_REFUSED_FOLLOWUP_REQUIRED",
                discipline=canonical_discipline,
            )

        return refusal

    # -----------------------------------------------------
    # NON-REFUSABLE → STAFF REMINDER
    # -----------------------------------------------------
    if canonical_discipline in NON_REFUSABLE_DISCIPLINES:
        _create_task_if_missing(
            db=db,
            patient=patient,
            user_id=user_id,
            now=now,
            task_type=TaskType.OTHER,
            task_status=TaskStatus.PENDING,
            alert_reason=f"{canonical_discipline}_VISIT_REFUSED_RESCHEDULE_REQUIRED",
            discipline=canonical_discipline,
        )

        return refusal

    return refusal
