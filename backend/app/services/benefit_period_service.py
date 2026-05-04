from datetime import timedelta
from sqlalchemy.orm import Session

from app.services.recert_f2f_tasks import seed_recert_f2f_tasks_for_benefit_period
from app.models.benefit_period import BenefitPeriod
from app.models.task import Task


def create_benefit_period(
    db: Session,
    *,
    patient_id: str,
    start_date,
    period_number: int,
):
    """
    Create a benefit period and seed required compliance tasks.
    BP1/BP2 = 90 days, BP3+ = 60 days.
    """

    # Determine CMS period length
    length_days = 90 if period_number in (1, 2) else 60
    end_date = start_date + timedelta(days=length_days - 1)

    benefit_period = BenefitPeriod(
        patient_id=patient_id,
        start_date=start_date,
        end_date=end_date,
        period_number=period_number,
        status="active",
    )

    db.add(benefit_period)
    db.flush()  # ✅ benefit_period.id now exists

    # ✅ Seed CERT / RECERT / F2F tasks (date-derived BP index)
    seed_recert_f2f_tasks_for_benefit_period(db, benefit_period=benefit_period)

    # ✅ Seed IDG_REVIEW task
    idg_task = Task(
        patient_id=patient_id,
        benefit_period_id=benefit_period.id,
        task_type="IDG_REVIEW",
        origin="PERIODIC",
        discipline="RN",
        regulatory_basis="IDG",
        due_date=start_date + timedelta(days=14),
        status="PENDING",
    )
    db.add(idg_task)

    db.commit()
    return benefit_period