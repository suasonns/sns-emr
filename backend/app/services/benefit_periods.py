from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.services.benefit_period_resolver import (
    BenefitPeriodRow,
    get_active_benefit_period,
)


def get_current_benefit_period(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    as_of_day: date,
) -> BenefitPeriodRow | None:
    """
    Canonical benefit period lookup.

    Enterprise rules:
    - Deterministic (no guessing, no heuristics).
    - Schema-tolerant via resolver layer.
    - Safe when no benefit period exists (returns None).
    - Read-only (no mutation).
    """

    if db is None:
        raise ValueError("db session is required")
    if not tenant_id:
        raise ValueError("tenant_id is required")
    if not patient_id:
        raise ValueError("patient_id is required")
    if not as_of_day:
        raise ValueError("as_of_day is required")

    return get_active_benefit_period(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        as_of_date=as_of_day,
    )
