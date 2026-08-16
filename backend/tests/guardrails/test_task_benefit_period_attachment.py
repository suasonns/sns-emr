from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.models.patient import Patient
from app.models.task import Task
from app.models.enums import (
    TaskType,
    TaskOrigin,
    TaskDiscipline,
    TaskRegulatoryBasis,
)
from app.services.benefit_period_service import rollover_benefit_period
from app.services.task_benefit_period_linker import attach_active_benefit_period_to_task


@pytest.fixture
def tenant_id(db_session):
    tenant_id = db_session.execute(
        text("SELECT id FROM tenants ORDER BY id LIMIT 1")
    ).scalar()

    assert tenant_id is not None
    return tenant_id


@pytest.fixture
def patient(db_session, tenant_id):
    user_id = db_session.execute(
        text("SELECT id FROM users LIMIT 1")
    ).scalar()

    assert user_id is not None
    
    patient = Patient(
        tenant_id=tenant_id,
        created_by=user_id,
        mrn=f"TASKTEST-{uuid4().hex[:8]}",
        date_of_birth=date(1950, 1, 1),
        primary_diagnosis="Terminal condition",
        status="ACTIVE",
        admission_status="PRE_REFERRAL",
    )
    db_session.add(patient)
    db_session.flush()
    return patient


def test_task_attaches_to_active_benefit_period(db_session, tenant_id, patient):
    bp = rollover_benefit_period(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        election_date=date(2026, 1, 1),
        start_date=date(2026, 1, 1),
        benefit_type="INITIAL",
    )

    task = Task(
        tenant_id=tenant_id,
        patient_id=patient.id,
        task_type=TaskType.IDG_REVIEW,
        origin=TaskOrigin.PERIODIC,
        discipline=TaskDiscipline.RN,
        regulatory_basis=TaskRegulatoryBasis.IDG_REVIEW,
        due_date=date(2026, 1, 15),  # ✅ FIXED
    )

    attach_active_benefit_period_to_task(
        db_session,
        task=task,
        tenant_id=tenant_id,
        patient_id=patient.id,
    )

    db_session.add(task)
    db_session.commit()

    assert task.benefit_period_id == bp.id


def test_task_attachment_does_not_override_existing_campaign(db_session, tenant_id, patient):
    bp1 = rollover_benefit_period(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        election_date=date(2026, 1, 1),
        start_date=date(2026, 1, 1),
        benefit_type="INITIAL",
    )

    bp2 = rollover_benefit_period(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        election_date=date(2026, 4, 1),
        start_date=date(2026, 4, 1),
        benefit_type="RECERT",
    )

    task = Task(
        tenant_id=tenant_id,
        patient_id=patient.id,
        benefit_period_id=bp1.id,
        task_type=TaskType.IDG_REVIEW,
        origin=TaskOrigin.PERIODIC,
        discipline=TaskDiscipline.RN,
        regulatory_basis=TaskRegulatoryBasis.IDG_REVIEW,  # ✅ FIXED
        due_date=date(2026, 4, 10),
    )

    attach_active_benefit_period_to_task(
        db_session,
        task=task,
        tenant_id=tenant_id,
        patient_id=patient.id,
    )

    db_session.add(task)
    db_session.commit()

    assert task.benefit_period_id == bp1.id


def test_task_without_active_bp_remains_unassigned(db_session, tenant_id, patient):
    task = Task(
        tenant_id=tenant_id,
        patient_id=patient.id,
        task_type=TaskType.IDG_REVIEW,
        origin=TaskOrigin.PERIODIC,
        discipline=TaskDiscipline.RN,
        regulatory_basis=TaskRegulatoryBasis.IDG_REVIEW,  # ✅ FIXED
        due_date=date(2026, 1, 15),
    )

    attach_active_benefit_period_to_task(
        db_session,
        task=task,
        tenant_id=tenant_id,
        patient_id=patient.id,
    )

    db_session.add(task)
    db_session.commit()

    assert task.benefit_period_id is None


def test_tasks_after_rollover_attach_to_new_bp(db_session, tenant_id, patient):
    bp1 = rollover_benefit_period(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        election_date=date(2026, 1, 1),
        start_date=date(2026, 1, 1),
        benefit_type="INITIAL",
    )

    bp2 = rollover_benefit_period(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        election_date=date(2026, 4, 1),
        start_date=date(2026, 4, 1),
        benefit_type="RECERT",
    )

    task = Task(
        tenant_id=tenant_id,
        patient_id=patient.id,
        task_type=TaskType.IDG_REVIEW,
        origin=TaskOrigin.PERIODIC,
        discipline=TaskDiscipline.RN,
        regulatory_basis=TaskRegulatoryBasis.IDG_REVIEW,  # ✅ FIXED
        due_date=date(2026, 4, 15),
    )

    attach_active_benefit_period_to_task(
        db_session,
        task=task,
        tenant_id=tenant_id,
        patient_id=patient.id,
    )

    db_session.add(task)
    db_session.commit()

    assert task.benefit_period_id == bp2.id