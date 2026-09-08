from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from app.models.admission import Admission
from app.models.enums import TaskOrigin, TaskRegulatoryBasis, TaskStatus, TaskType
from app.models.patient import Patient
from app.models.task import Task
from app.models.visit import Visit
from app.services.hope_phase_b_engine import (
    TASK_TYPE_HUV1,
    TASK_TYPE_HUV2,
    designate_visit_as_huv,
    detect_huv_designation_opportunity,
)
from tests.conftest import TEST_USER_ID


def _make_patient(db_session, tenant_id):
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"HUV-{uuid.uuid4().hex[:12]}",
        date_of_birth=date(1941, 7, 4),
        primary_diagnosis="Chronic systolic (congestive) heart failure",
        status="ACTIVE",
        admission_status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _make_admission(db_session, patient, tenant_id, election_date: datetime):
    admission = Admission(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient.id,
        admission_date=election_date,
        effective_date=election_date,
        election_signed_at=election_date,
        soc_date=election_date,
        status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(admission)
    db_session.commit()
    return admission


def _make_visit(db_session, patient, admission, tenant_id, *, visit_datetime, discipline="RN", finalized=True):
    visit = Visit(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient.id,
        admission_id=admission.id,
        provider_id=TEST_USER_ID,
        visit_type=discipline,
        visit_discipline=discipline,
        visit_datetime=visit_datetime,
        status="FINALIZED" if finalized else "DRAFT",
        finalized_at=visit_datetime if finalized else None,
        created_by=TEST_USER_ID,
    )
    db_session.add(visit)
    db_session.commit()
    return visit


def _make_huv_task(db_session, patient, tenant_id, huv_type: str, *, due_at: datetime):
    task = Task(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient.id,
        task_type=getattr(TaskType, huv_type),
        origin=TaskOrigin.SYSTEM,
        discipline="RN",
        regulatory_basis=TaskRegulatoryBasis.CONDITION_TRIGGER,
        status=TaskStatus.PENDING,
        due_at=due_at,
        due_date=due_at.date(),
    )
    db_session.add(task)
    db_session.commit()
    return task


def test_detect_huv1_opportunity_within_window(db_session):
    tenant_id = db_session.info.get("tenant_id")
    election_date = datetime(2026, 3, 1, 8, 0, tzinfo=timezone.utc)
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id, election_date)
    _make_huv_task(db_session, patient, tenant_id, TASK_TYPE_HUV1, due_at=election_date + timedelta(days=15))

    visit = _make_visit(
        db_session, patient, admission, tenant_id,
        visit_datetime=election_date + timedelta(days=8),
    )

    opportunity = detect_huv_designation_opportunity(
        db=db_session, tenant_id=tenant_id, patient_id=patient.id, visit=visit,
    )
    assert opportunity is not None
    assert opportunity["huv_type"] == TASK_TYPE_HUV1
    assert opportunity["day_number"] == 8


def test_detect_returns_none_outside_any_window(db_session):
    tenant_id = db_session.info.get("tenant_id")
    election_date = datetime(2026, 3, 1, 8, 0, tzinfo=timezone.utc)
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id, election_date)
    _make_huv_task(db_session, patient, tenant_id, TASK_TYPE_HUV1, due_at=election_date + timedelta(days=15))

    visit = _make_visit(
        db_session, patient, admission, tenant_id,
        visit_datetime=election_date + timedelta(days=2),
    )

    opportunity = detect_huv_designation_opportunity(
        db=db_session, tenant_id=tenant_id, patient_id=patient.id, visit=visit,
    )
    assert opportunity is None


def test_detect_returns_none_when_huv_already_completed(db_session):
    tenant_id = db_session.info.get("tenant_id")
    election_date = datetime(2026, 3, 1, 8, 0, tzinfo=timezone.utc)
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id, election_date)
    task = _make_huv_task(db_session, patient, tenant_id, TASK_TYPE_HUV1, due_at=election_date + timedelta(days=15))
    task.status = TaskStatus.COMPLETED
    db_session.add(task)
    db_session.commit()

    visit = _make_visit(
        db_session, patient, admission, tenant_id,
        visit_datetime=election_date + timedelta(days=8),
    )

    opportunity = detect_huv_designation_opportunity(
        db=db_session, tenant_id=tenant_id, patient_id=patient.id, visit=visit,
    )
    assert opportunity is None


def test_designate_visit_as_huv1_completes_task_with_audit_metadata(db_session):
    tenant_id = db_session.info.get("tenant_id")
    election_date = datetime(2026, 3, 1, 8, 0, tzinfo=timezone.utc)
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id, election_date)
    task = _make_huv_task(db_session, patient, tenant_id, TASK_TYPE_HUV1, due_at=election_date + timedelta(days=15))

    visit = _make_visit(
        db_session, patient, admission, tenant_id,
        visit_datetime=election_date + timedelta(days=8),
    )

    completed_task = designate_visit_as_huv(
        db=db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        visit=visit,
        huv_type=TASK_TYPE_HUV1,
        selected_by=TEST_USER_ID,
        reason="RN visit satisfied HUV1 clinically",
    )

    assert completed_task.id == task.id
    assert completed_task.status == TaskStatus.COMPLETED
    assert completed_task.completed_by == TEST_USER_ID
    assert completed_task.completion_reference_id == visit.id
    assert completed_task.completion_metadata["designation_reason"] == "RN visit satisfied HUV1 clinically"
    assert completed_task.completion_metadata["day_number"] == 8
    assert completed_task.completion_metadata["original_visit_type"] == "RN"


def test_designate_visit_outside_window_raises(db_session):
    tenant_id = db_session.info.get("tenant_id")
    election_date = datetime(2026, 3, 1, 8, 0, tzinfo=timezone.utc)
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id, election_date)
    _make_huv_task(db_session, patient, tenant_id, TASK_TYPE_HUV1, due_at=election_date + timedelta(days=15))

    visit = _make_visit(
        db_session, patient, admission, tenant_id,
        visit_datetime=election_date + timedelta(days=2),
    )

    with pytest.raises(ValueError, match="HUV1 must be completed"):
        designate_visit_as_huv(
            db=db_session,
            tenant_id=tenant_id,
            patient_id=patient.id,
            visit=visit,
            huv_type=TASK_TYPE_HUV1,
            selected_by=TEST_USER_ID,
        )


def test_designate_visit_already_satisfied_raises(db_session):
    tenant_id = db_session.info.get("tenant_id")
    election_date = datetime(2026, 3, 1, 8, 0, tzinfo=timezone.utc)
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id, election_date)
    task = _make_huv_task(db_session, patient, tenant_id, TASK_TYPE_HUV1, due_at=election_date + timedelta(days=15))
    task.status = TaskStatus.COMPLETED
    db_session.add(task)
    db_session.commit()

    visit = _make_visit(
        db_session, patient, admission, tenant_id,
        visit_datetime=election_date + timedelta(days=8),
    )

    with pytest.raises(ValueError, match="already satisfied"):
        designate_visit_as_huv(
            db=db_session,
            tenant_id=tenant_id,
            patient_id=patient.id,
            visit=visit,
            huv_type=TASK_TYPE_HUV1,
            selected_by=TEST_USER_ID,
        )


def test_designate_visit_non_rn_discipline_raises(db_session):
    tenant_id = db_session.info.get("tenant_id")
    election_date = datetime(2026, 3, 1, 8, 0, tzinfo=timezone.utc)
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id, election_date)
    _make_huv_task(db_session, patient, tenant_id, TASK_TYPE_HUV1, due_at=election_date + timedelta(days=15))

    visit = _make_visit(
        db_session, patient, admission, tenant_id,
        visit_datetime=election_date + timedelta(days=8),
        discipline="LVN",
    )

    with pytest.raises(ValueError, match="HUV must be completed by RN"):
        designate_visit_as_huv(
            db=db_session,
            tenant_id=tenant_id,
            patient_id=patient.id,
            visit=visit,
            huv_type=TASK_TYPE_HUV1,
            selected_by=TEST_USER_ID,
        )
