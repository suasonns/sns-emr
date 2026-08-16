import uuid
from datetime import datetime, timezone, timedelta

import pytest
from sqlalchemy import text

from app.models.patient import Patient
from app.models.task import Task
from app.models.enums import TaskType, TaskStatus

from app.services.admission_authorization_service import (
    record_records_release_consent,
    authorize_admission,
    TASK_INITIAL_RN_ICA,
    TASK_NOE_DUE,
)

_UUID_NS = uuid.UUID("11111111-1111-1111-1111-111111111111")

def _pick_user_id(db_session):
    user_id = db_session.execute(
        text("SELECT id FROM users LIMIT 1")
    ).scalar()

    assert user_id is not None
    return user_id

def stable_uuid(name: str) -> uuid.UUID:
    return uuid.uuid5(_UUID_NS, name)


FIXED_SOC = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)


def _ensure_min_patient(db_session, patient_id: uuid.UUID) -> Patient:
    """
    Create a minimal Patient row if not present.

    IMPORTANT:
    - patients.admission_status is NOT NULL
    - patients.created_by is NOT NULL
    """
    p = db_session.get(Patient, patient_id)
    if p:
        return p

    tenant_id = db_session.info.get("tenant_id")
    assert tenant_id, "db_session.info['tenant_id'] must be set by test harness"

    user_id = _pick_user_id(db_session)

    p = Patient(
        id=patient_id,
        tenant_id=tenant_id,
        mrn=f"MRN-{str(patient_id)[:8]}",
        date_of_birth=datetime(1950, 1, 1, tzinfo=timezone.utc).date(),
        primary_diagnosis="TEST DX",
        status="ACTIVE",
        admission_status="PRE_REFERRAL",
        acuity_state="ROUTINE",
        created_by=user_id,
    )

    db_session.add(p)
    db_session.commit()

    return p

def _tasks_for_patient(db_session, patient_id: uuid.UUID):
    tenant_id = db_session.info.get("tenant_id")
    return (
        db_session.query(Task)
        .filter(Task.tenant_id == tenant_id, Task.patient_id == patient_id)
        .all()
    )


def _assert_tasktype_enum_has_values(db_session):
    """
    Hard guard: If DB enum doesn't include new values, nothing else is meaningful.
    """
    assert hasattr(TaskType, TASK_INITIAL_RN_ICA), f"TaskType missing {TASK_INITIAL_RN_ICA} in app.models.enums"
    assert hasattr(TaskType, TASK_NOE_DUE), f"TaskType missing {TASK_NOE_DUE} in app.models.enums"

    rows = db_session.execute(
        text("SELECT unnest(enum_range(NULL::tasktype))")
    ).fetchall()
    values = {r[0] for r in rows}

    assert TASK_INITIAL_RN_ICA in values, f"DB enum tasks_task_type_enum missing {TASK_INITIAL_RN_ICA}"
    assert TASK_NOE_DUE in values, f"DB enum tasks_task_type_enum missing {TASK_NOE_DUE}"


@pytest.mark.core_rule("SOC / Admission / Tasks")
def test_records_release_creates_no_tasks(db_session):
    _assert_tasktype_enum_has_values(db_session)

    patient_id = stable_uuid("patient:records_release_only")
    _ensure_min_patient(db_session, patient_id)

    record_records_release_consent(
        db_session,
        patient_id=patient_id,
        signed_at=FIXED_SOC,
        user_id=None,
    )
    db_session.commit()

    tasks = _tasks_for_patient(db_session, patient_id)
    assert tasks == [], "Records-release consent must not generate ICA/NOE tasks"


@pytest.mark.core_rule("SOC / Admission / Tasks")
def test_authorize_sets_soc_and_creates_rn_ica_and_noe_tasks(db_session):
    _assert_tasktype_enum_has_values(db_session)

    patient_id = stable_uuid("patient:authorize_admission")
    p = _ensure_min_patient(db_session, patient_id)

    authorize_admission(
        db_session,
        patient_id=patient_id,
        election_signed_at=FIXED_SOC,
        authorized_by_user_id=None,
    )

    db_session.commit()
    db_session.refresh(p)

    # --------------------------------------------------
    # ✅ VERIFY ADMISSION (AUTHORITATIVE SOURCE)
    # --------------------------------------------------
    admission = (
        db_session.query(Admission)
        .filter(Admission.patient_id == patient_id)
        .order_by(Admission.created_at.desc())
        .first()
    )

    assert admission is not None, "Admission record must be created"

    # SOC must be stored on Admission, not Patient
    assert admission.soc_date.date() == FIXED_SOC.date()

    # Admission state must live on Admission
    assert admission.status in ("ADMITTED", "PENDING", "AUTHORIZED")

    # Election timestamp belongs to admission workflow
    assert admission.election_signed_at == FIXED_SOC

    # Ensure effective date consistency
    assert admission.effective_date is not None

    # --------------------------------------------------
    # ✅ VERIFY PATIENT (LIMITED ROLE ONLY)
    # --------------------------------------------------
    # Patient is NOT source of truth anymore
    assert p.id == patient_id
    assert hasattr(p, "updated_at")

    # --------------------------------------------------
    # ✅ VERIFY TASKS
    # --------------------------------------------------
    tasks = _tasks_for_patient(db_session, patient_id)
    by_type = {t.task_type: t for t in tasks}

    rn_type = getattr(TaskType, TASK_INITIAL_RN_ICA)
    noe_type = getattr(TaskType, TASK_NOE_DUE)

    assert rn_type in by_type, "RN ICA task not created"
    assert noe_type in by_type, "NOE task not created"

    rn_task = by_type[rn_type]
    noe_task = by_type[noe_type]

    assert rn_task.status in (
        TaskStatus.PENDING,
        TaskStatus.OVERDUE,
        TaskStatus.ESCALATED,
    )

    assert noe_task.status in (
        TaskStatus.PENDING,
        TaskStatus.OVERDUE,
        TaskStatus.ESCALATED,
    )

    # RN ICA due in 48 hours
    assert rn_task.due_at == FIXED_SOC + timedelta(hours=48)
    assert rn_task.due_date == (FIXED_SOC + timedelta(hours=48)).date()

    # NOE due in 5 days
    assert noe_task.due_at == FIXED_SOC + timedelta(days=5)
    assert noe_task.due_date == (FIXED_SOC + timedelta(days=5)).date()


@pytest.mark.core_rule("SOC / Admission / Tasks")
def test_authorize_is_idempotent_no_duplicate_open_tasks(db_session):
    _assert_tasktype_enum_has_values(db_session)

    patient_id = stable_uuid("patient:authorize_idempotent")
    _ensure_min_patient(db_session, patient_id)

    authorize_admission(
        db_session,
        patient_id=patient_id,
        election_signed_at=FIXED_SOC,
        authorized_by_user_id=None,
    )
    db_session.commit()

    authorize_admission(
        db_session,
        patient_id=patient_id,
        election_signed_at=FIXED_SOC,
        authorized_by_user_id=None,
    )
    db_session.commit()

    tasks = _tasks_for_patient(db_session, patient_id)

    rn_type = getattr(TaskType, TASK_INITIAL_RN_ICA)
    noe_type = getattr(TaskType, TASK_NOE_DUE)

    rn_count = sum(1 for t in tasks if t.task_type == rn_type and t.status == TaskStatus.PENDING)
    noe_count = sum(1 for t in tasks if t.task_type == noe_type and t.status == TaskStatus.PENDING)

    assert rn_count == 1, f"Expected exactly 1 open RN ICA task, found {rn_count}"
    assert noe_count == 1, f"Expected exactly 1 open NOE task, found {noe_count}"