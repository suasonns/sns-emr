# backend/app/services/benefit_period_service.py

from __future__ import annotations

from datetime import date, timedelta
from typing import Literal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.benefit_period import BenefitPeriod
from app.models.enums import (
    TaskDiscipline,
    TaskOrigin,
    TaskRegulatoryBasis,
    TaskType,
)
from app.models.task import Task
from app.services.task_benefit_period_linker import (
    attach_active_benefit_period_to_task,
)

AllowedBenefitType = Literal["INITIAL", "RECERT"]


def _cms_benefit_period_length_days(period_number: int) -> int:
    """
    CMS hospice election periods:
    - BP1: 90 days
    - BP2: 90 days
    - BP3+: 60 days
    """
    if period_number in (1, 2):
        return 90
    return 60


def rollover_benefit_period(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    election_date: date,
    start_date: date,
    benefit_type: AllowedBenefitType,
) -> BenefitPeriod:
    """
    Enterprise-grade benefit period rollover.

    Guarantees:
    - Only one current benefit period per patient
    - Old current BP is closed before new BP becomes current
    - Safe retry behavior for the same rollover request
    - Runs inside a single DB transaction
    """

    if benefit_type not in ("INITIAL", "RECERT"):
        raise ValueError("benefit_type must be 'INITIAL' or 'RECERT'")

    try:
        # ---------------------------------------------------------
        # 1. Lock all BP rows for this patient/tenant
        # ---------------------------------------------------------
        existing_rows = (
            db.query(BenefitPeriod)
            .filter(
                BenefitPeriod.patient_id == patient_id,
                BenefitPeriod.tenant_id == tenant_id,
            )
            .with_for_update()
            .all()
        )

        # ---------------------------------------------------------
        # 2. Idempotency check
        # ---------------------------------------------------------
        for row in existing_rows:
            if (
                row.start_date == start_date
                and row.benefit_type == benefit_type
                and row.tenant_id == tenant_id
                and row.patient_id == patient_id
            ):
                return row

        # ---------------------------------------------------------
        # 3. Find current BP
        # ---------------------------------------------------------
        current_bp = next((r for r in existing_rows if r.is_current), None)

        # ---------------------------------------------------------
        # 4. Validate chronology
        # ---------------------------------------------------------
        if current_bp and start_date < current_bp.start_date:
            raise ValueError(
                "start_date cannot be earlier than current BP start_date"
            )

        # ---------------------------------------------------------
        # 5. Compute next period number
        # ---------------------------------------------------------
        if not existing_rows:
            next_period_number = 1
        else:
            next_period_number = max(r.period_number for r in existing_rows) + 1

        # ---------------------------------------------------------
        # 6. Close current BP
        # ---------------------------------------------------------
        if current_bp:
            current_bp.is_current = False

            if current_bp.end_date is None:
                current_bp.end_date = start_date - timedelta(days=1)

        # ---------------------------------------------------------
        # 7. Compute CMS end date
        # ---------------------------------------------------------
        length_days = _cms_benefit_period_length_days(next_period_number)
        end_date = start_date + timedelta(days=length_days - 1)

        # ---------------------------------------------------------
        # 8. Create next/current BP
        # ---------------------------------------------------------
        new_bp = BenefitPeriod(
            tenant_id=tenant_id,
            patient_id=patient_id,
            benefit_type=benefit_type,
            period_number=next_period_number,
            election_date=election_date,
            start_date=start_date,
            end_date=end_date,
            is_current=True,
        )

        db.add(new_bp)
        db.flush()

        # ---------------------------------------------------------
        # 9. Seed IDG_REVIEW task for the new BP
        # ---------------------------------------------------------
        idg_task = Task(
            tenant_id=tenant_id,
            patient_id=patient_id,
            benefit_period_id=new_bp.id,
            task_type=TaskType.IDG_REVIEW,
            origin=TaskOrigin.PERIODIC,
            discipline=TaskDiscipline.RN,
            regulatory_basis=TaskRegulatoryBasis.IDG_REVIEW,
            due_date=start_date + timedelta(days=14),
        )

        # Safe no-op if already linked
        attach_active_benefit_period_to_task(
            db,
            task=idg_task,
            tenant_id=tenant_id,
            patient_id=patient_id,
            as_of_date=idg_task.due_date,
        )

        db.add(idg_task)

        # ---------------------------------------------------------
        # 10. Commit atomically
        # ---------------------------------------------------------
        db.commit()

        return new_bp

    except Exception:
        db.rollback()
        raise