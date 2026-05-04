
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.task import Task
from app.models.benefit_period import BenefitPeriod


def bp_index_date_derived(db: Session, patient_id, benefit_period_id) -> int:
    bps = (
        db.query(BenefitPeriod)
        .filter(BenefitPeriod.patient_id == patient_id)
        .order_by(BenefitPeriod.start_date.asc())
        .all()
    )
    for idx, bp in enumerate(bps, start=1):
        if str(bp.id) == str(benefit_period_id):
            return idx
    return 1


def require_f2f_completed_for_bp3_plus(db: Session, *, patient_id, benefit_period_id):
    idx = bp_index_date_derived(db, patient_id, benefit_period_id)
    if idx < 3:
        return  # BP1/BP2: no F2F requirement

    f2f_task = (
        db.query(Task)
        .filter(
            Task.patient_id == patient_id,
            Task.benefit_period_id == benefit_period_id,
            Task.task_type == "F2F",
        )
        .order_by(Task.created_at.desc())
        .first()
    )

    if not f2f_task or f2f_task.status != "COMPLETED":
        raise HTTPException(
            status_code=400,
            detail="F2F is required and must be completed before recertification for BP3+.",
        )


def complete_task_with_evidence(
    db: Session,
    *,
    patient_id,
    benefit_period_id,
    task_type: str,
    ref_type: str,
    ref_id: str,
):
    task = (
        db.query(Task)
        .filter(
            Task.patient_id == patient_id,
            Task.benefit_period_id == benefit_period_id,
            Task.task_type == task_type,
            Task.status == "PENDING",
        )
        .order_by(Task.due_date.asc())
        .first()
    )
    if not task:
        return None

    task.status = "COMPLETED"
    task.completed_at = datetime.utcnow()
    task.completion_reference_type = ref_type
    task.completion_reference_id = ref_id
    return task


def validate_f2f_window(db: Session, *, benefit_period_id, encounter_date: date):
    bp = db.query(BenefitPeriod).filter(BenefitPeriod.id == benefit_period_id).first()
    if not bp:
        raise HTTPException(status_code=404, detail="Benefit period not found")

    idx = bp_index_date_derived(db, bp.patient_id, benefit_period_id)

    # ✅ Only enforce 30-day window for BP3+
    if idx < 3:
        return

    earliest = bp.start_date - timedelta(days=30)
    latest = bp.start_date

    if not (earliest <= encounter_date <= latest):
        raise HTTPException(
            status_code=400,
            detail=(
                f"F2F encounter_date must be within 30 days prior to benefit period start "
                f"({earliest} to {latest})."
            ),
        )