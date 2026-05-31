import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import text

from app.models.patient import Patient
from app.models.task import Task
from app.models.enums import TaskType, TaskStatus, CompletionReferenceType

from app.services.admission_authorization_service import authorize_admission
from app.services.task_completion_evidence import complete_task_with_evidence


_UUID_NS = uuid.UUID("11111111-1111-1111-1111-111111111111")


def stable_uuid(name: str) -> uuid.UUID:
    return uuid.uuid5(_UUID_NS, name)


FIXED_SOC = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)


def _ensure_min_patient(db_session, patient_id: uuid.UUID) -> Patient:
    p = db_session.get(Patient, patient_id)
    if p:
        return p

    tenant_id = db_session.info.get("tenant_id")
    assert tenant_id

    p = Patient(
        id=patient_id,
        tenant_id=tenant_id,
        mrn=f"MRN-{str(patient_id)[:8]}",
        full_name="TEST PATIENT",
        date_of_birth=datetime(1950, 1, 1, tzinfo=timezone.utc).date(),
        primary_diagnosis="TEST DX",
        status="ACTIVE",
        admission_status="PRE_REFERRAL",
        acuity_state="ROUTINE",
    )
    db_session.add(p)
    db_session.commit()
    return p


def _get_task(db_session, patient_id: uuid.UUID, task_type: TaskType) -> Task:
    tenant_id = db_session.info.get("tenant_id")
    task = (
        db_session.query(Task)
        .filter(Task.tenant_id == tenant_id, Task.patient_id == patient_id, Task.task_type == task_type)
        .first()
    )
    assert task, f"Task {task_type} not found"
    return task


@pytest.mark.core_rule("Task completion evidence")
def test_cannot_complete_task_without_evidence(db_session):
    patient_id = stable_uuid("patient:noe_no_evidence")
    _ensure_min_patient(db_session, patient_id)

    authorize_admission(
        db_session,
        patient_id=patient_id,
        election_signed_at=FIXED_SOC,
        authorized_by_user_id=None,
    )
    db_session.commit()

    noe_task = _get_task(db_session, patient_id, TaskType.NOE_DUE)

    with pytest.raises(Exception) as ex:
        complete_task_with_evidence(
            db_session,
            task_id=noe_task.id,
            completion_reference_type=None,  # invalid
            completion_reference_id=None,    # invalid
            completed_by=None,
        )

    assert "Completion requires evidence" in str(ex.value)


@pytest.mark.core_rule("Task completion evidence")
def test_complete_task_with_evidence_sets_fields(db_session):
    patient_id = stable_uuid("patient:noe_with_evidence")
    _ensure_min_patient(db_session, patient_id)

    authorize_admission(
        db_session,
        patient_id=patient_id,
        election_signed_at=FIXED_SOC,
        authorized_by_user_id=None,
    )
    db_session.commit()

    noe_task = _get_task(db_session, patient_id, TaskType.NOE_DUE)

    doc_id = stable_uuid("document:noe_proof")

    complete_task_with_evidence(
        db_session,
        task_id=noe_task.id,
        completion_reference_type=CompletionReferenceType.DOCUMENT,
        completion_reference_id=doc_id,
        completed_by=None,
    )
    db_session.commit()

    db_session.refresh(noe_task)

    assert noe_task.status == TaskStatus.COMPLETED
    assert noe_task.completed_at is not None
    assert noe_task.completion_reference_type == CompletionReferenceType.DOCUMENT
    assert noe_task.completion_reference_id == doc_id