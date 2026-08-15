# services/idg_remediation.py
from __future__ import annotations

from typing import List, Dict

from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.enums import (
    TaskType,
    TaskStatus,
    TaskOrigin,
    TaskDiscipline,
)
from app.services.idg_compliance import get_idg_compliance_summary


# =========================================================
# MAP COMPLIANCE ISSUE → TASK TYPE
# =========================================================

def _map_reason_to_task(reason: str):

    if reason == "NO_REVIEW":
        return "CREATE_IDG"

    if reason == "NOT_FINALIZED":
        return "FINALIZE_IDG"

    if reason == "NO_POC_LINK":
        return "UPDATE_POC"

    if reason == "NO_MD_ATTESTATION":
        return "OBTAIN_MD_SIGNATURE"

    if reason.startswith("MISSING_DISCIPLINES"):
        return "COMPLETE_DISCIPLINE_DOCUMENTATION"

    if reason == "OUTDATED":
        return "SCHEDULE_NEW_IDG"

    return "UNKNOWN_REMEDIATION"


# =========================================================
# CHECK EXISTING REMEDIATION TASK
# =========================================================

def _remediation_task_exists(
    db: Session,
    *,
    patient_id,
    reason,
) -> bool:

    return (
        db.query(Task)
        .filter(
            Task.patient_id == patient_id,
            Task.task_type == TaskType.IDG_REMEDIATION,
            Task.status == TaskStatus.PENDING,
            Task.description == reason,
        )
        .first()
        is not None
    )


# =========================================================
# CREATE ONE REMEDIATION TASK
# =========================================================

def create_remediation_task(
    db: Session,
    *,
    tenant_id,
    patient_id,
    reason: str,
) -> Task | None:

    if _remediation_task_exists(
        db=db,
        patient_id=patient_id,
        reason=reason,
    ):
        return None

    task = Task(
        tenant_id=tenant_id,
        patient_id=patient_id,

        task_type=TaskType.IDG_REMEDIATION,
        status=TaskStatus.PENDING,

        origin=TaskOrigin.SYSTEM,
        discipline=TaskDiscipline.IDG_TEAM,

        description=reason,  # store reason clearly

    )

    db.add(task)
    return task


# =========================================================
# GENERATE REMEDIATION TASKS FROM COMPLIANCE
# =========================================================

def generate_remediation_tasks(
    db: Session,
    *,
    tenant_id,
) -> List[Task]:

    compliance_data = get_idg_compliance_summary(
        db=db,
        tenant_id=tenant_id,
    )

    created_tasks: List[Task] = []

    for row in compliance_data:

        if row["compliant"]:
            continue

        patient_id = row["patient_id"]
        reason = row["reason"]

        action_type = _map_reason_to_task(reason)

        task = create_remediation_task(
            db=db,
            tenant_id=tenant_id,
            patient_id=patient_id,
            reason=action_type,
        )

        if task:
            created_tasks.append(task)

    return created_tasks

