import uuid

from sqlalchemy import text

from datetime import datetime, timezone, timedelta

import pytest

from app.models.patient import Patient
from app.models.task import Task
from app.models.enums import TaskType, TaskStatus, CompletionReferenceType
from app.services.admission_authorization_service import authorize_admission
from app.services.task_completion_evidence import complete_task_with_evidence


_UUID_NS = uuid.UUID("11111111-1111-1111-1111-111111111111")


def stable_uuid(name: str) -> uuid.UUID:
    return uuid.uuid5(_UUID_NS, name)


SOC = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)

def _pick_user_id(db_session):
    user_id = db_session.execute(
        text("SELECT id FROM users LIMIT 1")
    ).scalar()

    assert user_id is not None
    return user_id

def _ensure_patient(db_session, pid: uuid.UUID):
    p = db_session.get(Patient, pid)
    if p:
        return p

    tenant_id = db_session.info.get("tenant_id")
    assert tenant_id
    user_id = _pick_user_id(db_session)

    p = Patient(
        id=pid,
        tenant_id=tenant_id,
        mrn=f"MRN-{str(pid)[:8]}",
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


def _get_open_idg(db_session, pid: uuid.UUID):
    tenant_id = db_session.info.get("tenant_id")
    return (
        db_session.query(Task)
        .filter(
            Task.tenant_id == tenant_id,
            Task.patient_id == pid,
            Task.task_type == TaskType.IDG_REVIEW,
            Task.status == TaskStatus.PENDING,
        )
        .first()
    )


@pytest.mark.core_rule("IDG review cadence")
def test_idg_task_created_on_admission_due_soc_plus_15(db_session):
    pid = stable_uuid("patient:idg_on_admission")
    _ensure_patient(db_session, pid)

    authorize_admission(
        db_session,
        patient_id=pid,
        election_signed_at=SOC,
        authorized_by_user_id=None,
    )
    db_session.commit()

    t = _get_open_idg(db_session, pid)
    assert t is not None, "IDG_REVIEW task must be created on admission"
    assert t.due_at.astimezone(timezone.utc).date() == (SOC + timedelta(days=15)).date()


@pytest.mark.core_rule("IDG review cadence")
def test_idg_completion_schedules_next_due_plus_15(db_session):
    pid = stable_uuid("patient:idg_next")
    _ensure_patient(db_session, pid)

    authorize_admission(
        db_session,
        patient_id=pid,
        election_signed_at=SOC,
        authorized_by_user_id=None,
    )
    db_session.commit()

    t = _get_open_idg(db_session, pid)
    assert t is not None

    evidence_id = stable_uuid("document:idg_minutes")
    complete_task_with_evidence(
        db_session,
        task_id=t.id,
        completion_reference_type=CompletionReferenceType.DOCUMENT,
        completion_reference_id=evidence_id,
        completed_by=None,
    )
    db_session.commit()

    next_t = _get_open_idg(db_session, pid)
    assert next_t is not None, "Next IDG_REVIEW task must be scheduled after completion"

    expected_date = (
        t.completed_at.astimezone(timezone.utc) + timedelta(days=15)
    ).date()
    actual_date = next_t.due_at.astimezone(timezone.utc).date()

    assert actual_date == expected_date