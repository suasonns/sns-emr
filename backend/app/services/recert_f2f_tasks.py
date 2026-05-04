from sqlalchemy.orm import Session

from app.models.benefit_period import BenefitPeriod
from app.models.task import Task


def _bp_index_for_period(db: Session, *, patient_id, benefit_period_id) -> int:
    """
    Date-derived benefit period index:
      1 = BP1, 2 = BP2, 3+ = BP3+
    """
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


def seed_recert_f2f_tasks_for_benefit_period(db: Session, *, benefit_period: BenefitPeriod):
    """
    Seeds Recert/F2F tasks when a benefit period is created.

    Rules (date-derived index):
      BP1: (optional) CERTIFICATION task
      BP2: RECERTIFICATION task
      BP3+: F2F task + RECERTIFICATION task

    Notes:
      - task_type enum must include CERTIFICATION, RECERTIFICATION, F2F
      - regulatory_basis enum uses CERTIFICATION and F2F (already in your DB)
    """
    patient_id = benefit_period.patient_id
    bp_index = _bp_index_for_period(db, patient_id=patient_id, benefit_period_id=benefit_period.id)
    start_date = benefit_period.start_date

    # Assign ownership discipline (MD is typical; NP also valid)
    owner = "MD"

    # --- BP1: optional CTI/certification task (audit-friendly) ---
    if bp_index == 1:
        db.add(
            Task(
                patient_id=patient_id,
                benefit_period_id=benefit_period.id,
                task_type="CERTIFICATION",
                origin="ADMISSION",
                discipline=owner,
                regulatory_basis="CERTIFICATION",
                due_date=start_date,
                status="PENDING",
            )
        )
        return

    # --- BP2: recertification required ---
    if bp_index == 2:
        db.add(
            Task(
                patient_id=patient_id,
                benefit_period_id=benefit_period.id,
                task_type="RECERTIFICATION",
                origin="PERIODIC",
                discipline=owner,
                regulatory_basis="CERTIFICATION",
                due_date=start_date,
                status="PENDING",
            )
        )
        return

    # --- BP3+: F2F + recertification required ---
    db.add(
        Task(
            patient_id=patient_id,
            benefit_period_id=benefit_period.id,
            task_type="F2F",
            origin="PERIODIC",
            discipline=owner,
            regulatory_basis="F2F",
            due_date=start_date,
            status="PENDING",
        )
    )

    db.add(
        Task(
            patient_id=patient_id,
            benefit_period_id=benefit_period.id,
            task_type="RECERTIFICATION",
            origin="PERIODIC",
            discipline=owner,
            regulatory_basis="CERTIFICATION",
            due_date=start_date,
            status="PENDING",
        )
    )
