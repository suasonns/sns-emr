import uuid
from datetime import datetime, timezone, timedelta

import pytest
from sqlalchemy import text

from app.models.patient import Patient
from app.models.visit import Visit
from app.models.task import Task
from app.models.enums import (
    TaskType,
    TaskStatus,
    TaskOrigin,
    TaskDiscipline,
    TaskRegulatoryBasis,
    CompletionReferenceType,
)

_UUID_NS = uuid.UUID("11111111-1111-1111-1111-111111111111")


def stable_uuid(name: str) -> uuid.UUID:
    return uuid.uuid5(_UUID_NS, name)


def utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


ROUTINE_VISIT_TIME = utc(datetime(2026, 1, 10, 10, 0, 0, tzinfo=timezone.utc))
CRISIS_VISIT_TIME = utc(datetime(2026, 1, 11, 10, 0, 0, tzinfo=timezone.utc))


def _ensure_min_patient(db_session, patient_id: uuid.UUID) -> Patient:
    p = db_session.get(Patient, patient_id)
    if p:
        return p

    tenant_id = db_session.info.get("tenant_id")
    assert tenant_id, "db_session.info['tenant_id'] must be set by test harness"

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


def _pick_provider_id(db_session, tenant_id: uuid.UUID) -> uuid.UUID:
    """
    Enterprise-safe provider resolution for visits.provider_id NOT NULL.

    Tries in order:
    1) providers table (if exists)
    2) users table (if exists)
    3) existing visits.provider_id (if any)
    Otherwise skip the test suite (schema has strict FK with no seed data).
    """
    # 1) providers table
    try:
        row = db_session.execute(
            text("SELECT id FROM providers WHERE tenant_id = :t LIMIT 1"),
            {"t": str(tenant_id)},
        ).fetchone()
        if row and row[0]:
            return row[0]
    except Exception:
        pass

    # 2) users table
    try:
        row = db_session.execute(
            text("SELECT id FROM users WHERE tenant_id = :t LIMIT 1"),
            {"t": str(tenant_id)},
        ).fetchone()
        if row and row[0]:
            return row[0]
    except Exception:
        pass

    # 3) existing visits provider_id
    try:
        row = db_session.execute(
            text("SELECT provider_id FROM visits WHERE tenant_id = :t LIMIT 1"),
            {"t": str(tenant_id)},
        ).fetchone()
        if row and row[0]:
            return row[0]
    except Exception:
        pass

    pytest.skip(
        "Cannot create Visit: visits.provider_id is NOT NULL but no provider/user seed exists. "
        "Seed a provider/user for this tenant or create a provider fixture."
    )


def _create_visit(
    db_session,
    *,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
    visit_id: uuid.UUID,
    visit_time: datetime,
    acuity_at_visit: str,
    is_supervisory: bool,
) -> Visit:
    provider_id = _pick_provider_id(db_session, tenant_id)

    v = Visit(
        id=visit_id,
        tenant_id=tenant_id,
        patient_id=patient_id,
        provider_id=provider_id,  # ✅ REQUIRED NOT NULL
        visit_type="RN",
        visit_discipline="RN",
        acuity_state_at_visit=acuity_at_visit,
        is_supervisory=is_supervisory,
        visit_datetime=visit_time,
        status="DRAFT",
    )
    db_session.add(v)
    db_session.commit()
    return v


def _finalize_visit(db_session, visit_id: uuid.UUID):
    """
    Deterministic policy test: mimic finalize side effects then call the policy hook directly.
    """
    from app.services.poc_update_automation import on_visit_finalized_apply_poc_policy

    v = db_session.query(Visit).filter(Visit.id == visit_id).one()
    p = db_session.query(Patient).filter(Patient.id == v.patient_id).one()

    now = datetime.now(timezone.utc)
    v.status = "FINALIZED"
    v.finalized_at = now
    db_session.flush()

    on_visit_finalized_apply_poc_policy(
        db=db_session,
        visit=v,
        patient=p,
        finalized_by_user_id=None,
    )
    db_session.commit()
    return v, p


def _tasks_for_patient(db_session, patient_id: uuid.UUID):
    tenant_id = db_session.info.get("tenant_id")
    return (
        db_session.query(Task)
        .filter(Task.tenant_id == tenant_id, Task.patient_id == patient_id)
        .order_by(Task.created_at.desc())
        .all()
    )


def _latest_task_of_type(db_session, patient_id: uuid.UUID, task_type: TaskType):
    tasks = _tasks_for_patient(db_session, patient_id)
    for t in tasks:
        if t.task_type == task_type:
            return t
    return None


@pytest.mark.core_rule("POC_UPDATE automation")
def test_routine_supervisory_rn_finalize_creates_poc_update_due_plus_14_days(db_session):
    tenant_id = db_session.info.get("tenant_id")
    patient_id = stable_uuid("patient:routine_poc")
    _ensure_min_patient(db_session, patient_id)

    visit_id = stable_uuid("visit:routine_supervisory")
    _create_visit(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient_id,
        visit_id=visit_id,
        visit_time=ROUTINE_VISIT_TIME,
        acuity_at_visit="ROUTINE",
        is_supervisory=True,
    )

    _finalize_visit(db_session, visit_id)

    t = _latest_task_of_type(db_session, patient_id, TaskType.POC_UPDATE)
    assert t is not None, "ROUTINE supervisory RN finalize must create POC_UPDATE task"

    assert t.status == TaskStatus.PENDING
    assert t.origin == TaskOrigin.PERIODIC
    assert t.discipline == TaskDiscipline.RN
    assert t.regulatory_basis == TaskRegulatoryBasis.POC_UPDATE

    expected_due = ROUTINE_VISIT_TIME + timedelta(days=14)
    assert t.due_at == expected_due
    assert t.due_date == expected_due.date()


@pytest.mark.core_rule("POC_UPDATE automation")
def test_routine_non_supervisory_rn_finalize_does_not_create_poc_update(db_session):
    tenant_id = db_session.info.get("tenant_id")
    patient_id = stable_uuid("patient:routine_non_supervisory_no_poc")
    _ensure_min_patient(db_session, patient_id)

    visit_id = stable_uuid("visit:routine_non_supervisory")
    _create_visit(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient_id,
        visit_id=visit_id,
        visit_time=ROUTINE_VISIT_TIME,
        acuity_at_visit="ROUTINE",
        is_supervisory=False,
    )

    _finalize_visit(db_session, visit_id)

    t = _latest_task_of_type(db_session, patient_id, TaskType.POC_UPDATE)
    assert t is None, "ROUTINE non-supervisory RN finalize must not create POC_UPDATE task"


@pytest.mark.core_rule("POC_UPDATE automation")
def test_crisis_rn_finalize_creates_and_completes_poc_update_with_visit_evidence(db_session):
    tenant_id = db_session.info.get("tenant_id")
    patient_id = stable_uuid("patient:crisis_poc")
    p = _ensure_min_patient(db_session, patient_id)

    # Put patient in an active crisis window
    p.acuity_state = "CRISIS"
    p.crisis_started_at = CRISIS_VISIT_TIME - timedelta(days=1)
    p.crisis_ended_at = None
    db_session.commit()

    visit_id = stable_uuid("visit:crisis_rn")
    _create_visit(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient_id,
        visit_id=visit_id,
        visit_time=CRISIS_VISIT_TIME,
        acuity_at_visit="CRISIS",
        is_supervisory=False,
    )

    v, _ = _finalize_visit(db_session, visit_id)

    t = _latest_task_of_type(db_session, patient_id, TaskType.POC_UPDATE)
    assert t is not None, "CRISIS RN finalize must create POC_UPDATE task"

    assert t.origin == TaskOrigin.MANUAL
    assert t.discipline == TaskDiscipline.RN
    assert t.regulatory_basis == TaskRegulatoryBasis.POC_UPDATE

    # Crisis auto-complete with visit evidence
    assert t.status == TaskStatus.COMPLETED
    assert t.completed_at is not None
    assert t.completion_reference_type == CompletionReferenceType.VISIT
    assert t.completion_reference_id == v.id

    # Due same day as visit
    assert t.due_at is not None
    assert t.due_at.date() == CRISIS_VISIT_TIME.date()


@pytest.mark.core_rule("POC_UPDATE automation")
def test_poc_update_is_idempotent_no_duplicate_open_tasks(db_session):
    tenant_id = db_session.info.get("tenant_id")
    patient_id = stable_uuid("patient:poc_idempotent")
    _ensure_min_patient(db_session, patient_id)

    visit_id = stable_uuid("visit:routine_supervisory_idempotent")
    _create_visit(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient_id,
        visit_id=visit_id,
        visit_time=ROUTINE_VISIT_TIME,
        acuity_at_visit="ROUTINE",
        is_supervisory=True,
    )

    _finalize_visit(db_session, visit_id)
    _finalize_visit(db_session, visit_id)

    tasks = _tasks_for_patient(db_session, patient_id)
    open_poc = [
        t for t in tasks
        if t.task_type == TaskType.POC_UPDATE and t.status == TaskStatus.PENDING
    ]

    assert len(open_poc) == 1, f"Expected exactly 1 open POC_UPDATE task, found {len(open_poc)}"