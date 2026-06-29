from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.sfv_requirement import SFVRequirement
from app.models.enums import TaskType, TaskStatus, CompletionReferenceType

logger = logging.getLogger(__name__)

ELIGIBLE_SFV_COMPLETION_DISCIPLINES = {"RN", "LVN"}


# =========================================================
# ✅ TIMEZONE SAFETY HELPER
# =========================================================
def _as_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Normalize any datetime into timezone-aware UTC.
    """
    if dt is None:
        return None

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


# =========================================================
# MAIN FUNCTION
# =========================================================
def complete_open_sfv_for_visit(
    *,
    db: Session,
    visit,
    user_id,
):
    """
    Complete ONE open SFV task + ONE open SFV requirement.

    Rules:
    - RN / LVN only
    - Same patient
    - Not ICA visit
    - Within 48 hrs
    """

    if visit is None:
        return None

    visit_discipline = str(getattr(visit, "visit_discipline", "") or "").strip().upper()
    if visit_discipline not in ELIGIBLE_SFV_COMPLETION_DISCIPLINES:
        logger.info(
            "SFV_COMPLETION: visit discipline not eligible visit_id=%s discipline=%s",
            str(getattr(visit, "id", None)),
            visit_discipline,
        )
        return None

    tenant_id = getattr(visit, "tenant_id", None)
    patient_id = getattr(visit, "patient_id", None)
    visit_id = getattr(visit, "id", None)

    if not tenant_id or not patient_id or not visit_id:
        logger.warning("SFV_COMPLETION: missing identifiers visit_id=%s", str(visit_id))
        return None

    # ✅ normalize visit datetime
    visit_dt = _as_utc(getattr(visit, "visit_datetime", None)) or _as_utc(datetime.now())

    # =========================================================
    # FIND OPEN REQUIREMENT
    # =========================================================
    open_requirement = (
        db.query(SFVRequirement)
        .filter(
            SFVRequirement.tenant_id == tenant_id,
            SFVRequirement.patient_id == patient_id,
            SFVRequirement.status == "PENDING",
        )
        .order_by(SFVRequirement.trigger_date.asc())
        .first()
    )

    if not open_requirement:
        logger.info("SFV_COMPLETION: no requirement found")
        return None

    # ✅ skip same visit
    if str(open_requirement.triggering_visit_id) == str(visit_id):
        logger.info("SFV_COMPLETION: skipping same ICA visit")
        return None

    trigger_dt = _as_utc(open_requirement.trigger_date)

    logger.info(
        "SFV_DEBUG: requirement_id=%s trigger_visit=%s current_visit=%s",
        str(open_requirement.id),
        str(open_requirement.triggering_visit_id),
        str(visit_id),
    )

    if trigger_dt is None:
        logger.warning("SFV_COMPLETION: missing trigger_date")
        return None

    # =========================================================
    # ✅ FIXED COMPARISON (NO MIXED TIMEZONES)
    # =========================================================
    if visit_dt > trigger_dt + timedelta(hours=48):
        logger.info("SFV_COMPLETION: outside 48hr window")
        return None

    # =========================================================
    # FIND TASK
    # =========================================================
    open_task = (
        db.query(Task)
        .filter(
            Task.tenant_id == tenant_id,
            Task.patient_id == patient_id,
            Task.task_type == TaskType.SFV,
            Task.status.in_([
                TaskStatus.PENDING,
                TaskStatus.IN_PROGRESS,
                TaskStatus.OVERDUE,
            ]),
        )
        .order_by(Task.created_at.asc())
        .first()
    )

    # =========================================================
    # COMPLETE REQUIREMENT
    # =========================================================
    open_requirement.status = "COMPLETED"
    open_requirement.completed_visit_id = visit_id
    open_requirement.updated_at = visit_dt

    logger.info(
        "SFV_COMPLETION: requirement completed %s",
        str(open_requirement.id),
    )

    # =========================================================
    # COMPLETE TASK
    # =========================================================
    if open_task:
        open_task.status = TaskStatus.COMPLETED
        open_task.completed_at = visit_dt
        open_task.completion_reference_type = CompletionReferenceType.VISIT
        open_task.completion_reference_id = visit_id
        open_task.updated_at = visit_dt

        if hasattr(open_task, "updated_by"):
            open_task.updated_by = user_id

        logger.info("SFV_COMPLETION: task completed %s", str(open_task.id))

    return {
        "requirement_id": str(open_requirement.id),
        "task_id": str(open_task.id) if open_task else None,
        "completed_by_visit_id": str(visit_id),
    }