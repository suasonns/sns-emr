# services/recert_f2f_enforcement.py

from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.benefit_period import BenefitPeriod
from app.models.task import Task
from app.models.enums import (
    TaskStatus,
    TaskType,
)


def bp_index_date_derived(
    db: Session,
    *,
    patient_id,
    tenant_id,
    benefit_period_id,
) -> int:
    """
    Date-derived benefit period index.

    BP1 = first benefit period
    BP2 = second benefit period
    BP3+ = all subsequent benefit periods
    """

    bps = (
        db.query(BenefitPeriod)
        .filter(
            BenefitPeriod.patient_id == patient_id,
            BenefitPeriod.tenant_id == tenant_id,
        )
        .order_by(BenefitPeriod.start_date.asc())
        .all()
    )

    for idx, bp in enumerate(bps, start=1):
        if bp.id == benefit_period_id:
            return idx

    return 1


def require_f2f_completed_for_bp3_plus(
    db: Session,
    *,
    patient_id,
    tenant_id,
    benefit_period_id,
) -> None:
    """
    BP3+ requires completed F2F prior to recertification.
    """

    idx = bp_index_date_derived(
        db,
        patient_id=patient_id,
        tenant_id=tenant_id,
        benefit_period_id=benefit_period_id,
    )

    if idx < 3:
        return

    f2f_task = (
        db.query(Task)
        .filter(
            Task.tenant_id == tenant_id,
            Task.patient_id == patient_id,
            Task.benefit_period_id == benefit_period_id,
            Task.task_type == TaskType.F2F,
        )
        .order_by(Task.created_at.desc())
        .first()
    )

    if (
        not f2f_task
        or f2f_task.status != TaskStatus.COMPLETED
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "F2F is required and must be completed "
                "before recertification for BP3+."
            ),
        )


def complete_task_with_evidence(
    db: Session,
    *,
    tenant_id,
    patient_id,
    benefit_period_id,
    task_type,
    ref_type: str,
    ref_id: str,
):
    """
    Completes a task only when completion
    evidence is supplied.

    Caller owns transaction.
    """

    if not ref_type or not ref_id:
        raise HTTPException(
            status_code=400,
            detail="Completion evidence is required.",
        )

    task = (
        db.query(Task)
        .filter(
            Task.tenant_id == tenant_id,
            Task.patient_id == patient_id,
            Task.benefit_period_id == benefit_period_id,
            Task.task_type == task_type,
            Task.status == TaskStatus.PENDING,
        )
        .order_by(Task.due_date.asc())
        .first()
    )

    if not task:
        return None

    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.utcnow()
    task.completion_reference_type = ref_type
    task.completion_reference_id = ref_id

    return task


def validate_f2f_window(
    db: Session,
    *,
    benefit_period_id,
    encounter_date: date,
) -> None:
    """
    BP3+ requires F2F encounter
    within 30 days before the start
    of the benefit period.
    """

    bp = (
        db.query(BenefitPeriod)
        .filter(
            BenefitPeriod.id == benefit_period_id,
        )
        .first()
    )

    if not bp:
        raise HTTPException(
            status_code=404,
            detail="Benefit period not found",
        )

    idx = bp_index_date_derived(
        db,
        patient_id=bp.patient_id,
        tenant_id=bp.tenant_id,
        benefit_period_id=benefit_period_id,
    )

    if idx < 3:
        return

    earliest = bp.start_date - timedelta(days=30)
    latest = bp.start_date

    if not (earliest <= encounter_date <= latest):
        raise HTTPException(
            status_code=400,
            detail=(
                f"F2F encounter_date must be within "
                f"30 days prior to benefit period start "
                f"({earliest} to {latest})."
            ),
        )
