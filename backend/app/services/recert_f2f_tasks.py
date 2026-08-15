from sqlalchemy.orm import Session

from app.models.benefit_period import BenefitPeriod
from app.models.task import Task
from app.models.enums import (
    TaskType,
    TaskStatus,
    TaskOrigin,
    TaskRegulatoryBasis,
)


ACTIVE_STATUSES = [
    TaskStatus.PENDING,
    TaskStatus.IN_PROGRESS,
    TaskStatus.OVERDUE,
]


def _bp_index_for_period(
    db: Session,
    *,
    patient_id,
    tenant_id,
    benefit_period_id,
) -> int:
    """
    Date-derived benefit period index:
      1 = BP1
      2 = BP2
      3+ = BP3+
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


def _task_exists(
    db: Session,
    *,
    benefit_period_id,
    task_type,
) -> bool:
    return (
        db.query(Task.id)
        .filter(
            Task.benefit_period_id == benefit_period_id,
            Task.task_type == task_type,
            Task.status.in_(ACTIVE_STATUSES),
        )
        .first()
        is not None
    )


def seed_recert_f2f_tasks_for_benefit_period(
    db: Session,
    *,
    benefit_period: BenefitPeriod,
):
    """
    Production-grade task seeding.

    Rules:
      BP1  -> CERTIFICATION
      BP2  -> RECERTIFICATION
      BP3+ -> F2F + RECERTIFICATION

    Guarantees:
      - Idempotent
      - No duplicate task creation
      - Tenant-safe BP indexing
      - Enum-safe values
      - Caller controls transaction
    """

    patient_id = benefit_period.patient_id
    tenant_id = benefit_period.tenant_id
    start_date = benefit_period.start_date

    bp_index = _bp_index_for_period(
        db,
        patient_id=patient_id,
        tenant_id=tenant_id,
        benefit_period_id=benefit_period.id,
    )

    owner = "MD"

    # ---------------------------------------------------------
    # BP1
    # ---------------------------------------------------------
    if bp_index == 1:

        if not _task_exists(
            db,
            benefit_period_id=benefit_period.id,
            task_type=TaskType.CERTIFICATION,
        ):
            db.add(
                Task(
                    tenant_id=tenant_id,
                    patient_id=patient_id,
                    benefit_period_id=benefit_period.id,
                    task_type=TaskType.CERTIFICATION,
                    origin=TaskOrigin.ADMISSION,
                    discipline=owner,
                    regulatory_basis=TaskRegulatoryBasis.CERTIFICATION,
                    due_date=start_date,
                    status=TaskStatus.PENDING,
                )
            )

        return

    # ---------------------------------------------------------
    # BP2
    # ---------------------------------------------------------
    if bp_index == 2:

        if not _task_exists(
            db,
            benefit_period_id=benefit_period.id,
            task_type=TaskType.RECERTIFICATION,
        ):
            db.add(
                Task(
                    tenant_id=tenant_id,
                    patient_id=patient_id,
                    benefit_period_id=benefit_period.id,
                    task_type=TaskType.RECERTIFICATION,
                    origin=TaskOrigin.PERIODIC,
                    discipline=owner,
                    regulatory_basis=TaskRegulatoryBasis.CERTIFICATION,
                    due_date=start_date,
                    status=TaskStatus.PENDING,
                )
            )

        return

    # ---------------------------------------------------------
    # BP3+
    # ---------------------------------------------------------

    if not _task_exists(
        db,
        benefit_period_id=benefit_period.id,
        task_type=TaskType.F2F,
    ):
        db.add(
            Task(
                tenant_id=tenant_id,
                patient_id=patient_id,
                benefit_period_id=benefit_period.id,
                task_type=TaskType.F2F,
                origin=TaskOrigin.PERIODIC,
                discipline=owner,
                regulatory_basis=TaskRegulatoryBasis.F2F,
                due_date=start_date,
                status=TaskStatus.PENDING,
            )
        )

    if not _task_exists(
        db,
        benefit_period_id=benefit_period.id,
        task_type=TaskType.RECERTIFICATION,
    ):
        db.add(
            Task(
                tenant_id=tenant_id,
                patient_id=patient_id,
                benefit_period_id=benefit_period.id,
                task_type=TaskType.RECERTIFICATION,
                origin=TaskOrigin.PERIODIC,
                discipline=owner,
                regulatory_basis=TaskRegulatoryBasis.CERTIFICATION,
                due_date=start_date,
                status=TaskStatus.PENDING,
            )
        )