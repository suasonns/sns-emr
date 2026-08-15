# services/idg_dashboard_api.py

from __future__ import annotations

from typing import Dict
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.task import Task
from app.models.enums import TaskType, TaskStatus

from app.services.idg_compliance import (
    get_idg_compliance_summary,
    get_missed_idg_meetings,
)


# =========================================================
# IDG DASHBOARD METRICS
# =========================================================

def get_idg_dashboard_metrics(
    db: Session,
    *,
    tenant_id,
) -> Dict:

    # -----------------------------------------
    # TOTAL ACTIVE PATIENTS
    # -----------------------------------------
    total_patients = (
        db.query(Patient)
        .filter(
            Patient.tenant_id == tenant_id,
            Patient.status == "active",
        )
        .count()
    )

    # -----------------------------------------
    # COMPLIANCE SUMMARY
    # -----------------------------------------
    compliance_data = get_idg_compliance_summary(
        db=db,
        tenant_id=tenant_id,
    )

    compliant_count = sum(1 for x in compliance_data if x["compliant"])
    non_compliant_count = total_patients - compliant_count

    compliance_rate = (
        (compliant_count / total_patients) * 100
        if total_patients > 0 else 0
    )

    # -----------------------------------------
    # REASON BREAKDOWN
    # -----------------------------------------
    reason_counts = {}

    for row in compliance_data:
        reason = row["reason"]
        if reason not in reason_counts:
            reason_counts[reason] = 0
        reason_counts[reason] += 1

    # -----------------------------------------
    # MISSED IDG MEETINGS
    # -----------------------------------------
    missed_meetings = get_missed_idg_meetings(
        db=db,
        tenant_id=tenant_id,
    )

    missed_count = len(missed_meetings)

    # -----------------------------------------
    # TASK METRICS
    # -----------------------------------------
    now = datetime.now(timezone.utc)

    overdue_tasks = (
        db.query(Task)
        .filter(
            Task.tenant_id == tenant_id,
            Task.task_type == TaskType.IDG_REVIEW,
            Task.status == TaskStatus.PENDING,
            Task.due_at < now,
        )
        .count()
    )

    upcoming_tasks = (
        db.query(Task)
        .filter(
            Task.tenant_id == tenant_id,
            Task.task_type == TaskType.IDG_REVIEW,
            Task.status == TaskStatus.PENDING,
            Task.due_at >= now,
        )
        .count()
    )

    # -----------------------------------------
    # FINAL RESPONSE
    # -----------------------------------------
    return {
        "total_active_patients": total_patients,
        "compliant_patients": compliant_count,
        "non_compliant_patients": non_compliant_count,
        "compliance_rate": round(compliance_rate, 2),

        "missed_idg_meetings": missed_count,

        "overdue_idg_tasks": overdue_tasks,
        "upcoming_idg_tasks": upcoming_tasks,

        "compliance_reason_breakdown": reason_counts,
    }
