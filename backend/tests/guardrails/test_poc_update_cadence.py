from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

import pytest

from app.models.patient import Patient
from app.models.task import Task
from app.models.enums import (
    TaskType,
    TaskStatus,
    TaskOrigin,
    CompletionReferenceType,
)
from app.services.poc_update_automation import on_visit_finalized_apply_poc_policy


SYSTEM_TEST_USER_ID = uuid.UUID(
    "11111111-1111-1111-1111-111111111111"
)


def _tenant_id(db_session) -> uuid.UUID:
    """
    Resolve the tenant to use for this test run from the conftest.py
    db_session fixture's designated test tenant (never the real/live
    tenant) - see conftest.py's _test_tenant_id() for the safety
    rationale. Do not hardcode a tenant UUID here; that previously wrote
    synthetic POC-* patients directly into the live Love & Faith tenant.
    """
    return uuid.UUID(str(db_session.info.get("tenant_id")))

def stable_uuid(name: str) -> uuid.UUID:
    """Deterministic UUID helper for tests."""
    return uuid.uuid5(uuid.NAMESPACE_DNS, name)


def _utc(dt: datetime) -> datetime:
    return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _ensure_patient(db_session, patient_id: uuid.UUID, *, acuity_state: str = "ROUTINE") -> Patient:
    """
    Minimal patient seed compatible with the existing test DB schema.
    This is intentionally conservative and matches the patterns used elsewhere.
    """
    p = db_session.query(Patient).filter(Patient.id == patient_id).one_or_none()

    now = datetime.now(timezone.utc)

    if p is None:
        p = Patient(
            id=patient_id,
            tenant_id=_tenant_id(db_session),
            mrn=f"POC-{str(patient_id)[:8]}",
            date_of_birth=date(1940, 1, 1),
            primary_diagnosis="C34.90",
            status="ACTIVE",
            admission_status="PRE_REFERRAL",
            acuity_state=acuity_state,
            created_by=SYSTEM_TEST_USER_ID,
            created_at=now,
            updated_at=now,
        )
        db_session.add(p)
        db_session.flush()
    else:
        if hasattr(p, "acuity_state"):
            p.acuity_state = acuity_state
        if hasattr(p, "updated_at"):
            p.updated_at = now
        db_session.flush()

    return p


def _clear_poc_tasks(db_session, patient_id: uuid.UUID) -> None:
    db_session.query(Task).filter(
        Task.tenant_id == _tenant_id(db_session),
        Task.patient_id == patient_id,
        Task.task_type == TaskType.POC_UPDATE,
    ).delete(synchronize_session=False)
    db_session.flush()


def _poc_tasks(db_session, patient_id: uuid.UUID):
    return (
        db_session.query(Task)
        .filter(
            Task.tenant_id == _tenant_id(db_session),
            Task.patient_id == patient_id,
            Task.task_type == TaskType.POC_UPDATE,
        )
        .order_by(Task.created_at.asc())
        .all()
    )


@dataclass
class DummyVisit:
    id: uuid.UUID
    tenant_id: uuid.UUID
    patient_id: uuid.UUID
    visit_type: str = "RN"
    visit_discipline: str = "RN"
    visit_datetime: datetime = datetime.now(timezone.utc)
    finalized_at: datetime | None = None
    acuity_state_at_visit: str | None = None
    is_supervisory: bool = False


@pytest.mark.core_rule("POC_UPDATE cadence")
def test_routine_supervisory_rn_creates_poc_due_plus_14(db_session):
    patient_id = stable_uuid("patient:poc_routine_supervisory")
    patient = _ensure_patient(db_session, patient_id, acuity_state="ROUTINE")
    _clear_poc_tasks(db_session, patient_id)

    visit_time = _utc(datetime(2026, 6, 1, 10, 0, 0))
    visit = DummyVisit(
        id=stable_uuid("visit:poc_routine_supervisory"),
        tenant_id=_tenant_id(db_session),
        patient_id=patient_id,
        visit_type="RN",
        visit_discipline="RN",
        visit_datetime=visit_time,
        acuity_state_at_visit="ROUTINE",
        is_supervisory=True,
    )

    on_visit_finalized_apply_poc_policy(
        db_session,
        visit=visit,
        patient=patient,
        finalized_by_user_id=None,
    )
    db_session.commit()

    tasks = _poc_tasks(db_session, patient_id)
    assert len(tasks) == 1
    t = tasks[0]

    assert t.origin == TaskOrigin.PERIODIC
    assert t.status == TaskStatus.PENDING

    expected_due_date = (visit_time + timedelta(days=14)).date()
    if hasattr(t, "due_date") and t.due_date is not None:
        assert t.due_date == expected_due_date
    elif hasattr(t, "due_at") and t.due_at is not None:
        assert t.due_at.date() == expected_due_date

    if hasattr(t, "completion_reference_type"):
        assert t.completion_reference_type is None
    if hasattr(t, "completion_reference_id"):
        assert t.completion_reference_id is None


@pytest.mark.core_rule("POC_UPDATE cadence")
def test_routine_non_supervisory_rn_creates_no_poc(db_session):
    patient_id = stable_uuid("patient:poc_routine_non_supervisory")
    patient = _ensure_patient(db_session, patient_id, acuity_state="ROUTINE")
    _clear_poc_tasks(db_session, patient_id)

    visit_time = _utc(datetime(2026, 6, 1, 11, 0, 0))
    visit = DummyVisit(
        id=stable_uuid("visit:poc_routine_non_supervisory"),
        tenant_id=_tenant_id(db_session),
        patient_id=patient_id,
        visit_type="RN",
        visit_discipline="RN",
        visit_datetime=visit_time,
        acuity_state_at_visit="ROUTINE",
        is_supervisory=False,
    )

    on_visit_finalized_apply_poc_policy(
        db_session,
        visit=visit,
        patient=patient,
        finalized_by_user_id=None,
    )
    db_session.commit()

    tasks = _poc_tasks(db_session, patient_id)
    assert len(tasks) == 0


@pytest.mark.core_rule("POC_UPDATE cadence")
def test_crisis_rn_creates_and_completes_same_day_with_visit_evidence(db_session):
    patient_id = stable_uuid("patient:poc_crisis")
    patient = _ensure_patient(db_session, patient_id, acuity_state="CRISIS")
    _clear_poc_tasks(db_session, patient_id)

    visit_time = _utc(datetime(2026, 6, 2, 9, 30, 0))
    visit_id = stable_uuid("visit:poc_crisis")
    visit = DummyVisit(
        id=visit_id,
        tenant_id=_tenant_id(db_session),
        patient_id=patient_id,
        visit_type="RN",
        visit_discipline="RN",
        visit_datetime=visit_time,
        acuity_state_at_visit="CRISIS",
        is_supervisory=False,
    )

    on_visit_finalized_apply_poc_policy(
        db_session,
        visit=visit,
        patient=patient,
        finalized_by_user_id=None,
    )
    db_session.commit()

    tasks = _poc_tasks(db_session, patient_id)
    assert len(tasks) == 1
    t = tasks[0]

    assert t.origin == TaskOrigin.MANUAL
    assert t.status == TaskStatus.COMPLETED

    if hasattr(t, "completion_reference_type"):
        assert t.completion_reference_type == CompletionReferenceType.VISIT
    if hasattr(t, "completion_reference_id"):
        assert t.completion_reference_id == visit_id

    if hasattr(t, "due_date") and t.due_date is not None:
        assert t.due_date == visit_time.date()
    elif hasattr(t, "due_at") and t.due_at is not None:
        assert t.due_at.date() == visit_time.date()


@pytest.mark.core_rule("POC_UPDATE cadence")
def test_crisis_idempotent_repeat_finalize_does_not_duplicate(db_session):
    patient_id = stable_uuid("patient:poc_crisis_idempotent")
    patient = _ensure_patient(db_session, patient_id, acuity_state="CRISIS")
    _clear_poc_tasks(db_session, patient_id)

    visit_time = _utc(datetime(2026, 6, 2, 10, 0, 0))
    visit_id = stable_uuid("visit:poc_crisis_idempotent")
    visit = DummyVisit(
        id=visit_id,
        tenant_id=_tenant_id(db_session),
        patient_id=patient_id,
        visit_type="RN",
        visit_discipline="RN",
        visit_datetime=visit_time,
        acuity_state_at_visit="CRISIS",
        is_supervisory=False,
    )

    on_visit_finalized_apply_poc_policy(db_session, visit=visit, patient=patient, finalized_by_user_id=None)
    db_session.commit()

    on_visit_finalized_apply_poc_policy(db_session, visit=visit, patient=patient, finalized_by_user_id=None)
    db_session.commit()

    tasks = _poc_tasks(db_session, patient_id)
    assert len(tasks) == 1
    assert tasks[0].status == TaskStatus.COMPLETED


@pytest.mark.core_rule("POC_UPDATE cadence")
def test_routine_idempotent_repeat_finalize_does_not_duplicate(db_session):
    patient_id = stable_uuid("patient:poc_routine_idempotent")
    patient = _ensure_patient(db_session, patient_id, acuity_state="ROUTINE")
    _clear_poc_tasks(db_session, patient_id)

    visit_time = _utc(datetime(2026, 6, 3, 8, 0, 0))
    visit = DummyVisit(
        id=stable_uuid("visit:poc_routine_idempotent"),
        tenant_id=_tenant_id(db_session),
        patient_id=patient_id,
        visit_type="RN",
        visit_discipline="RN",
        visit_datetime=visit_time,
        acuity_state_at_visit="ROUTINE",
        is_supervisory=True,
    )

    on_visit_finalized_apply_poc_policy(db_session, visit=visit, patient=patient, finalized_by_user_id=None)
    db_session.commit()

    on_visit_finalized_apply_poc_policy(db_session, visit=visit, patient=patient, finalized_by_user_id=None)
    db_session.commit()

    tasks = _poc_tasks(db_session, patient_id)
    assert len(tasks) == 1
    assert tasks[0].status == TaskStatus.PENDING
