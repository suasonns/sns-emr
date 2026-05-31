import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from app.models.patient import Patient
from app.models.task import Task
from app.models.enums import TaskType

from app.services.admission_authorization_service import authorize_admission
from app.services.poc_update_automation import on_visit_finalized_apply_poc_policy


_UUID_NS = uuid.UUID("11111111-1111-1111-1111-111111111111")


def stable_uuid(name: str) -> uuid.UUID:
    return uuid.uuid5(_UUID_NS, name)


SOC = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)


def _ensure_patient(db_session, pid: uuid.UUID) -> Patient:
    p = db_session.get(Patient, pid)
    if p:
        return p

    tenant_id = db_session.info.get("tenant_id")
    assert tenant_id

    p = Patient(
        id=pid,
        tenant_id=tenant_id,
        mrn=f"MRN-{str(pid)[:8]}",
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


def _db_identity(db_session) -> str:
    """
    Must be called BEFORE any failing SQL.
    """
    try:
        return str(db_session.execute(text("select current_user")).scalar())
    except Exception:
        return "UNKNOWN_USER"


def _get_any_benefit_period(db_session, patient_id: uuid.UUID, db_user: str):
    """
    Read-only lookup. If the DB role cannot SELECT, SKIP instead of FAIL.

    IMPORTANT:
    If a SQL error occurs, SQLAlchemy marks the transaction as failed.
    We must rollback BEFORE doing anything else.
    """
    try:
        return db_session.execute(
            text(
                """
                SELECT id
                FROM public.benefit_periods
                WHERE patient_id = :pid
                ORDER BY start_date DESC
                LIMIT 1
                """
            ),
            {"pid": str(patient_id)},
        ).scalar()
    except ProgrammingError as e:
        msg = str(e).lower()
        # rollback immediately to clear failed transaction state
        try:
            db_session.rollback()
        except Exception:
            pass

        if "permission denied" in msg:
            pytest.skip(
                f"No SELECT privilege on public.benefit_periods for role '{db_user}'. "
                "Grant SELECT to the pytest DB role to enable this alignment guardrail."
            )
        raise


def _get_latest_task(db_session, patient_id: uuid.UUID, task_type: TaskType) -> Task | None:
    tenant_id = db_session.info.get("tenant_id")
    return (
        db_session.query(Task)
        .filter(
            Task.tenant_id == tenant_id,
            Task.patient_id == patient_id,
            Task.task_type == task_type,
        )
        .order_by(Task.created_at.desc())
        .first()
    )


@pytest.mark.core_rule("Benefit period alignment")
def test_idg_task_has_benefit_period_id_when_period_exists(db_session):
    pid = stable_uuid("patient:bp_idg")
    patient = _ensure_patient(db_session, pid)

    db_user = _db_identity(db_session)
    bp_id = _get_any_benefit_period(db_session, patient.id, db_user)

    if not bp_id:
        pytest.skip("No benefit period exists for patient; cannot assert alignment")

    authorize_admission(
        db_session,
        patient_id=patient.id,
        election_signed_at=SOC,
        authorized_by_user_id=None,
    )
    db_session.commit()

    idg_task = _get_latest_task(db_session, patient.id, TaskType.IDG_REVIEW)
    assert idg_task is not None
    assert idg_task.benefit_period_id == bp_id


@pytest.mark.core_rule("Benefit period alignment")
def test_poc_update_task_has_benefit_period_id_when_period_exists(db_session):
    pid = stable_uuid("patient:bp_poc")
    patient = _ensure_patient(db_session, pid)

    db_user = _db_identity(db_session)
    bp_id = _get_any_benefit_period(db_session, patient.id, db_user)

    if not bp_id:
        pytest.skip("No benefit period exists for patient; cannot assert alignment")

    visit = SimpleNamespace(
        id=stable_uuid("visit:bp_poc"),
        patient_id=patient.id,
        tenant_id=patient.tenant_id,
        visit_type="RN",
        visit_discipline="RN",
        is_supervisory=True,
        acuity_state_at_visit="ROUTINE",
        visit_datetime=SOC,
        finalized_at=SOC,
        status="FINALIZED",
    )

    on_visit_finalized_apply_poc_policy(
        db_session,
        visit=visit,
        patient=patient,
        finalized_by_user_id=None,
    )
    db_session.commit()

    poc_task = _get_latest_task(db_session, patient.id, TaskType.POC_UPDATE)
    assert poc_task is not None
    assert poc_task.benefit_period_id == bp_id