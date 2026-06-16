from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest

from app.models.patient import Patient
from app.models.task import Task
from app.models.enums import (
    TaskType,
    TaskStatus,
    TaskOrigin,
    TaskDiscipline,
    TaskRegulatoryBasis,
    CompletionReferenceType,
)
from app.services.task_completion_evidence import complete_task_with_evidence


TENANT_ID = uuid.UUID("01271980-0000-0000-0000-000005101977")


# -------------------------------------------------
# Deterministic helpers (enterprise-grade)
# -------------------------------------------------

def _fixed_due() -> datetime:
    """
    Far-future date avoids UNIQUE collisions across test re-runs:
    uq_poc_update_periodic_per_patient_due
    """
    return datetime(2099, 1, 1, 10, 0, 0, tzinfo=timezone.utc)


def _ensure_patient(db_session, patient_id: uuid.UUID) -> Patient:
    p = db_session.query(Patient).filter(Patient.id == patient_id).one_or_none()
    if p:
        return p

    now = datetime.now(timezone.utc)
    p = Patient(
        id=patient_id,
        tenant_id=TENANT_ID,
        mrn=f"EVI-{str(patient_id)[:8]}",
        full_name="Evidence Hardening Patient",
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="C34.90",
        status="ACTIVE",
        admission_status="PRE_REFERRAL",
        acuity_state="ROUTINE",
        created_at=now,
        updated_at=now,
    )
    db_session.add(p)
    db_session.flush()
    return p


def _clear_unique_poc_collision(db_session, patient_id: uuid.UUID) -> None:
    """
    Ensures deterministic behavior under a persistent DB by removing
    any prior row that would violate:
      UNIQUE(task_type, origin, patient_id, due_date)
    """
    due = _fixed_due()
    db_session.query(Task).filter(
        Task.tenant_id == TENANT_ID,
        Task.patient_id == patient_id,
        Task.task_type == TaskType.POC_UPDATE,
        Task.origin == TaskOrigin.PERIODIC,
        Task.due_date == due.date(),
    ).delete(synchronize_session=False)
    db_session.flush()


# -------------------------------------------------
# Tests
# -------------------------------------------------

@pytest.mark.core_rule("Task completion evidence")
def test_complete_requires_evidence(db_session):
    patient_id = uuid.uuid5(uuid.NAMESPACE_DNS, "patient:evidence_requires")
    _ensure_patient(db_session, patient_id)
    _clear_unique_poc_collision(db_session, patient_id)

    due = _fixed_due()

    task = Task(
        id=uuid.uuid4(),
        tenant_id=TENANT_ID,
        patient_id=patient_id,
        task_type=TaskType.POC_UPDATE,
        origin=TaskOrigin.PERIODIC,
        discipline=TaskDiscipline.RN,
        regulatory_basis=TaskRegulatoryBasis.POC_UPDATE,
        status=TaskStatus.PENDING,
        due_at=due,
        due_date=due.date(),
    )
    db_session.add(task)
    db_session.commit()

    with pytest.raises(Exception) as ex:
        complete_task_with_evidence(
            db_session,
            task_id=task.id,
            completion_reference_type=None,
            completion_reference_id=None,
            completed_by=None,
        )

    assert "Completion requires evidence" in str(ex.value)


@pytest.mark.core_rule("Task completion evidence")
def test_complete_sets_fields(db_session):
    patient_id = uuid.uuid5(uuid.NAMESPACE_DNS, "patient:evidence_sets")
    _ensure_patient(db_session, patient_id)
    _clear_unique_poc_collision(db_session, patient_id)

    due = _fixed_due()

    task = Task(
        id=uuid.uuid4(),
        tenant_id=TENANT_ID,
        patient_id=patient_id,
        task_type=TaskType.POC_UPDATE,
        origin=TaskOrigin.PERIODIC,
        discipline=TaskDiscipline.RN,
        regulatory_basis=TaskRegulatoryBasis.POC_UPDATE,
        status=TaskStatus.PENDING,
        due_at=due,
        due_date=due.date(),
    )
    db_session.add(task)
    db_session.commit()

    evidence_id = uuid.uuid4()

    complete_task_with_evidence(
        db_session,
        task_id=task.id,
        completion_reference_type=CompletionReferenceType.VISIT,
        completion_reference_id=evidence_id,
        completed_by=None,
        completed_at=datetime.now(timezone.utc),
    )
    db_session.commit()
    db_session.refresh(task)

    assert task.status == TaskStatus.COMPLETED
    assert task.completed_at is not None
    assert task.completion_reference_type == CompletionReferenceType.VISIT
    assert task.completion_reference_id == evidence_id