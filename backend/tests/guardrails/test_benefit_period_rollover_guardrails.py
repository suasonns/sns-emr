from __future__ import annotations

from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.models.patient import Patient
from app.models.benefit_period import BenefitPeriod
from app.models.task import Task
from app.models.enums import TaskType
from app.services.benefit_period_service import rollover_benefit_period


@pytest.fixture
def tenant_id(db_session):
    """
    Reuse any already-seeded tenant row in the test DB.
    This avoids guessing tenant table required columns.
    """
    tenant_id = db_session.execute(
        text("SELECT id FROM tenants ORDER BY id LIMIT 1")
    ).scalar()

    assert tenant_id is not None, "No tenant row found in test DB."
    return tenant_id


@pytest.fixture
def patient_id(db_session, tenant_id):
    """
    Create a minimal patient row using the currently shared Patient model.
    """
    user_id = db_session.execute(
        text("SELECT id FROM users LIMIT 1")
    ).scalar()

    assert user_id is not None
    
    patient = Patient(
        tenant_id=tenant_id,
        mrn=f"BPTEST-{uuid4().hex[:8]}",
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="Terminal illness",
        status="ACTIVE",
        admission_status="PRE_REFERRAL",
        created_by=user_id,
    )
    
    db_session.add(patient)
    db_session.flush()
    return patient.id


def _count_benefit_periods(db_session, *, tenant_id, patient_id) -> int:
    return (
        db_session.query(BenefitPeriod)
        .filter(
            BenefitPeriod.tenant_id == tenant_id,
            BenefitPeriod.patient_id == patient_id,
        )
        .count()
    )


def _count_current_benefit_periods(db_session, *, tenant_id, patient_id) -> int:
    return (
        db_session.query(BenefitPeriod)
        .filter(
            BenefitPeriod.tenant_id == tenant_id,
            BenefitPeriod.patient_id == patient_id,
            BenefitPeriod.is_current.is_(True),
        )
        .count()
    )


def _get_all_benefit_periods(db_session, *, tenant_id, patient_id):
    return (
        db_session.query(BenefitPeriod)
        .filter(
            BenefitPeriod.tenant_id == tenant_id,
            BenefitPeriod.patient_id == patient_id,
        )
        .order_by(BenefitPeriod.period_number.asc(), BenefitPeriod.start_date.asc())
        .all()
    )


def _count_idg_tasks_for_bp(
    db_session,
    *,
    tenant_id,
    patient_id,
    benefit_period_id,
) -> int:
    return (
        db_session.query(Task)
        .filter(
            Task.tenant_id == tenant_id,
            Task.patient_id == patient_id,
            Task.benefit_period_id == benefit_period_id,
            Task.task_type == TaskType.IDG_REVIEW,
        )
        .count()
    )


def test_first_benefit_period_creation(db_session, tenant_id, patient_id):
    """
    Guardrail:
    - creates BP1 when none exists
    - marks it current
    - assigns period_number = 1
    - seeds one IDG_REVIEW task
    """
    election_date = date(2026, 1, 1)
    start_date = date(2026, 1, 1)

    bp = rollover_benefit_period(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient_id,
        election_date=election_date,
        start_date=start_date,
        benefit_type="INITIAL",
    )

    db_session.refresh(bp)

    assert bp is not None
    assert bp.patient_id == patient_id
    assert bp.tenant_id == tenant_id
    assert bp.period_number == 1
    assert bp.benefit_type == "INITIAL"
    assert bp.election_date == election_date
    assert bp.start_date == start_date
    assert bp.end_date == start_date + timedelta(days=89)
    assert bp.is_current is True

    assert _count_benefit_periods(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient_id,
    ) == 1

    assert _count_current_benefit_periods(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient_id,
    ) == 1

    assert _count_idg_tasks_for_bp(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient_id,
        benefit_period_id=bp.id,
    ) == 1


def test_rollover_to_next_benefit_period(db_session, tenant_id, patient_id):
    """
    Guardrail:
    - BP1 becomes not current
    - BP2 becomes current
    - BP1 end_date closes the day before BP2 start_date
    """
    bp1 = rollover_benefit_period(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient_id,
        election_date=date(2026, 1, 1),
        start_date=date(2026, 1, 1),
        benefit_type="INITIAL",
    )

    bp2 = rollover_benefit_period(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient_id,
        election_date=date(2026, 4, 1),
        start_date=date(2026, 4, 1),
        benefit_type="RECERT",
    )

    db_session.refresh(bp1)
    db_session.refresh(bp2)

    assert bp1.period_number == 1
    assert bp1.is_current is False
    assert bp1.end_date == date(2026, 3, 31)

    assert bp2.period_number == 2
    assert bp2.is_current is True
    assert bp2.start_date == date(2026, 4, 1)
    assert bp2.end_date == date(2026, 6, 29)  # 90-day inclusive BP2

    all_rows = _get_all_benefit_periods(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient_id,
    )

    assert len(all_rows) == 2

    assert _count_current_benefit_periods(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient_id,
    ) == 1


def test_repeat_call_does_not_create_extra_benefit_period(db_session, tenant_id, patient_id):
    """
    Guardrail:
    - repeat call with identical business identity returns existing row
    - no duplicate BP is created
    """
    first = rollover_benefit_period(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient_id,
        election_date=date(2026, 1, 1),
        start_date=date(2026, 1, 1),
        benefit_type="INITIAL",
    )

    second = rollover_benefit_period(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient_id,
        election_date=date(2026, 1, 1),
        start_date=date(2026, 1, 1),
        benefit_type="INITIAL",
    )

    assert first.id == second.id

    assert _count_benefit_periods(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient_id,
    ) == 1

    assert _count_current_benefit_periods(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient_id,
    ) == 1


def test_only_one_current_benefit_period_remains_after_rollover(
    db_session,
    tenant_id,
    patient_id,
):
    """
    Guardrail:
    - after multiple legitimate rollovers, only one row remains current
    """
    rollover_benefit_period(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient_id,
        election_date=date(2026, 1, 1),
        start_date=date(2026, 1, 1),
        benefit_type="INITIAL",
    )

    rollover_benefit_period(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient_id,
        election_date=date(2026, 4, 1),
        start_date=date(2026, 4, 1),
        benefit_type="RECERT",
    )

    rollover_benefit_period(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient_id,
        election_date=date(2026, 6, 30),
        start_date=date(2026, 6, 30),
        benefit_type="RECERT",
    )

    current_rows = (
        db_session.query(BenefitPeriod)
        .filter(
            BenefitPeriod.tenant_id == tenant_id,
            BenefitPeriod.patient_id == patient_id,
            BenefitPeriod.is_current.is_(True),
        )
        .all()
    )

    assert len(current_rows) == 1
    assert current_rows[0].period_number == 3

    duplicate_currents = db_session.execute(
        text(
            """
            SELECT patient_id, COUNT(*)
            FROM benefit_periods
            WHERE is_current = true
            GROUP BY patient_id
            HAVING COUNT(*) > 1
            """
        )
    ).fetchall()

    assert duplicate_currents == []