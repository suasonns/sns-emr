import uuid
from datetime import datetime, timezone, timedelta

import pytest
from sqlalchemy import text

from app.models.patient import Patient
from app.models.task import Task
from app.models.enums import TaskType

from app.services.admission_authorization_service import (
    record_records_release_consent,
    authorize_admission,
    TASK_INITIAL_RN_ICA,
    TASK_NOE_DUE,
)

_UUID_NS = uuid.UUID("11111111-1111-1111-1111-111111111111")


def stable_uuid(name: str) -> uuid.UUID:
    return uuid.uuid5(_UUID_NS, name)


FIXED_SOC = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)


def _ensure_min_patient(db_session, patient_id: uuid.UUID) -> Patient:
    """
    Create a minimal Patient row if not present.
    Adjust fields here ONLY if your Patient model changes.
    """
    existing = db_session.get(Patient, patient_id)
    if existing:
        return existing

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

        # ✅ REQUIRED BY DB NOT NULL constraint
        admission_status="PRE_REFERRAL",

        acuity_state="ROUTINE",
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


def _assert_tasktype_enum_aligned(db_session):
    """
    HARD GUARD: Code enum must match DB enum.
    """
    rows = db_session.execute(
        text("SELECT unnest(enum_range(NULL::tasks_task_type_enum))")
    ).fetchall()

    db_values = {r[0] for r in rows}
    code_values = {e.value for e in TaskType}

    missing = db_values - code_values
    assert not missing, f"TaskType enum missing DB values: {missing}"


# ------------------------------------------------------------------
# TEST 1 — Records‑release creates NO tasks
# ------------------------------------------------------------------
@pytest.mark.core_rule("Admission Authorization")
def test_records_release_creates_no_tasks(db_session):
    _assert_tasktype_enum_aligned(db_session)

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
    assert tasks == [], "Records‑release must not create ICA or NOE tasks"


# ------------------------------------------------------------------
# TEST 2 — Authorize sets SOC and creates RN ICA + NOE tasks
# ------------------------------------------------------------------
@pytest.mark.core_rule("Admission Authorization")
def test_authorize_sets_soc_and_creates_tasks(db_session):
    _assert_tasktype_enum_aligned(db_session)

    patient_id = stable_uuid("patient:authorize")
    p = _ensure_min_patient(db_session, patient_id)

    authorize_admission(
        db_session,
        patient_id=patient_id,
        election_signed_at=FIXED_SOC,
        authorized_by_user_id=None,
    )
    db_session.commit()
    db_session.refresh(p)

    assert p.election_signed_at == FIXED_SOC
    assert p.soc_date == FIXED_SOC
    assert p.admission_status == "ADMITTED"

    tasks = _tasks_for_patient(db_session, patient_id)
    by_type = {t.task_type: t for t in tasks}

    rn_type = getattr(TaskType, TASK_INITIAL_RN_ICA)
    noe_type = getattr(TaskType, TASK_NOE_DUE)

    assert rn_type in by_type, "RN ICA task not created"
    assert noe_type in by_type, "NOE task not created"

    assert by_type[rn_type].due_at == FIXED_SOC + timedelta(hours=48)
    assert by_type[noe_type].due_at == FIXED_SOC + timedelta(days=5)


# ------------------------------------------------------------------
# TEST 3 — Authorize is idempotent (no duplicate tasks)
# ------------------------------------------------------------------
@pytest.mark.core_rule("Admission Authorization")
def test_authorize_is_idempotent(db_session):
    _assert_tasktype_enum_aligned(db_session)

    patient_id = stable_uuid("patient:idempotent")
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

    rn_count = sum(1 for t in tasks if t.task_type == rn_type)
    noe_count = sum(1 for t in tasks if t.task_type == noe_type)

    assert rn_count == 1, "Duplicate RN ICA task created"
    assert noe_count == 1, "Duplicate NOE task created"


# ------------------------------------------------------------------
# TEST 4 — SOC is IMMUTABLE once set
# ------------------------------------------------------------------
@pytest.mark.core_rule("Admission Authorization")
def test_soc_is_immutable(db_session):
    _assert_tasktype_enum_aligned(db_session)

    patient_id = stable_uuid("patient:soc_immutable")
    p = _ensure_min_patient(db_session, patient_id)

    authorize_admission(
        db_session,
        patient_id=patient_id,
        election_signed_at=FIXED_SOC,
        authorized_by_user_id=None,
    )
    db_session.commit()
    db_session.refresh(p)

    original_soc = p.soc_date

    # Attempt to re‑authorize with a different date
    authorize_admission(
        db_session,
        patient_id=patient_id,
        election_signed_at=FIXED_SOC + timedelta(days=1),
        authorized_by_user_id=None,
    )
    db_session.commit()
    db_session.refresh(p)

    assert p.soc_date == original_soc, "SOC must be immutable once set"