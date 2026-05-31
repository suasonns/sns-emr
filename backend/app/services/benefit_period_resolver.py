from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class BenefitPeriodRow:
    """
    Minimal, schema-tolerant result.
    """
    id: UUID
    patient_id: UUID
    start_date: date
    end_date: Optional[date]


def get_active_benefit_period(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    as_of_date: date,
) -> Optional[BenefitPeriodRow]:
    """
    Deterministic resolver:
    Return the single active benefit period for patient_id on as_of_date.

    Active rule:
      start_date <= as_of_date AND (end_date IS NULL OR end_date >= as_of_date)

    Enterprise guardrails:
    - Tenant-safe: join patients to enforce tenant scope
    - Deterministic: newest matching start_date wins
    - Integrity-safe: if >1 active periods overlap, raise ValueError
    - Permission-safe: if DB role lacks SELECT on benefit_periods, return None
      WITHOUT aborting the outer transaction (uses a SAVEPOINT).
    """

    sql = text(
        """
        SELECT
            bp.id AS id,
            bp.patient_id AS patient_id,
            bp.start_date AS start_date,
            bp.end_date AS end_date
        FROM public.benefit_periods bp
        JOIN public.patients p
          ON p.id = bp.patient_id
        WHERE p.tenant_id = :tenant_id
          AND bp.patient_id = :patient_id
          AND bp.start_date <= :as_of_date
          AND (bp.end_date IS NULL OR bp.end_date >= :as_of_date)
        ORDER BY bp.start_date DESC
        LIMIT 2
        """
    )

    try:
        # SAVEPOINT: prevents permission errors from aborting the outer transaction
        with db.begin_nested():
            rows = (
                db.execute(
                    sql,
                    {
                        "tenant_id": tenant_id,
                        "patient_id": patient_id,
                        "as_of_date": as_of_date,
                    },
                )
                .mappings()
                .all()
            )
    except ProgrammingError as e:
        # If benefit periods are not readable in this environment, treat as unavailable.
        # DO NOT raise; DO NOT rollback outer transaction.
        if "permission denied" in str(e).lower():
            return None
        raise

    if not rows:
        return None

    if len(rows) > 1:
        raise ValueError(
            f"Multiple active benefit periods found for patient {patient_id} on {as_of_date}. "
            "Benefit periods must not overlap."
        )

    r = rows[0]
    return BenefitPeriodRow(
        id=r["id"],
        patient_id=r["patient_id"],
        start_date=r["start_date"],
        end_date=r["end_date"],
    )
