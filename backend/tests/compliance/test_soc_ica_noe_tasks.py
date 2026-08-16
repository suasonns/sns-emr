import uuid
import pytest
from datetime import datetime, timezone, timedelta

from app.models.patient import Patient
from app.models.task import Task
from app.models.enums import TaskType
from app.services.admission_authorization_service import (
    record_records_release_consent,
    authorize_admission,
    TASK_INITIAL_RN_ICA,
    TASK_NOE_DUE,
)
from app.models.admission import Admission
from tests.conftest import TEST_USER_ID

_UUID_NS = uuid.UUID("11111111-1111-1111-1111-111111111111")


def stable_uuid(name: str) -> uuid.UUID:
    return uuid.uuid5(_UUID_NS, name)


FIXED_SOC = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)


def _ensure_min_patient(db_session, patient_id: uuid.UUID):
    p = db_session.get(Patient, patient_id)
    if p:
        return p

    # Minimal patient (match your schema constraints)
    p = Patient(
        id=patient_id,
        tenant_id=db_session.info.get("tenant_id"),
        mrn=f"MRN-{str(patient_id)[:8]}",
        date_of_birth=datetime(1950, 1, 1, tzinfo=timezone.utc).date(),
        primary_diagnosis="TEST DX",
        status="ACTIVE",
        acuity_state="ROUTINE",
    )
    db_session.add(p)
    db_session.commit()
    return p


def _task_types_for_patient(db_session, patient_id: uuid.UUID):
    tenant_id = db_session.info.get("tenant_id")
    tasks = (
        db_session.query(Task)
        .filter(Task.tenant_id == tenant_id, Task.patient_id == patient_id)
        .all()
    )
    return {t.task_type for t in tasks}


@pytest.mark.core_rule("SOC / ICA / NOE timing")
def test_records_release_does_not_create_ica_or_noe_tasks(db_session):
    patient_id = stable_uuid("patient:records_release_only")
    _ensure_min_patient(db_session, patient_id)

    record_records_release_consent(
        db_session,
        patient_id=patient_id,
        signed_at=FIXED_SOC,
        user_id=None,
    )
    db_session.commit()

    types = _task_types_for_patient(db_session, patient_id)
    assert TASK_INITIAL_RN_ICA not in types
    assert TASK_NOE_DUE not in types


@pytest.mark.core_rule("SOC / ICA / NOE timing")
def test_authorize_sets_soc_and_creates_rn_ica_and_noe_tasks(db_session):

    patient_id = stable_uuid("patient:authorize_admission")
    p = _ensure_min_patient(db_session, patient_id)

    authorize_admission(
        db_session,
        patient_id=patient_id,
        election_signed_at=FIXED_SOC,
        authorized_by_user_id=TEST_USER_ID,
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

    assert admission is not None, "Admission must exist after authorization"

    assert admission.soc_date is not None, "SOC must be set"
    assert admission.soc_date.date() == FIXED_SOC.date()

    assert admission.election_signed_at == FIXED_SOC

    assert admission.status in (
        "PENDING",
        "AUTHORIZED",
        "ADMITTED",
    )

    # --------------------------------------------------
    # ✅ VERIFY TASK CREATION
    # --------------------------------------------------
    tenant_id = db_session.info.get("tenant_id")

    tasks = (
        db_session.query(Task)
        .filter(
            Task.tenant_id == tenant_id,
            Task.patient_id == patient_id,
        )
        .all()
    )

    by_type = {t.task_type: t for t in tasks}

    rn_type = getattr(TaskType, TASK_INITIAL_RN_ICA)
    noe_type = getattr(TaskType, TASK_NOE_DUE)

    assert rn_type in by_type, "RN ICA task missing"
    assert noe_type in by_type, "NOE task missing"

    rn_task = by_type[rn_type]
    noe_task = by_type[noe_type]

    # --------------------------------------------------
    # ✅ VERIFY TIMING (REGULATORY CRITICAL)
    # --------------------------------------------------

    assert rn_task.due_at == FIXED_SOC + timedelta(hours=48)
    assert noe_task.due_at == FIXED_SOC + timedelta(days=5)