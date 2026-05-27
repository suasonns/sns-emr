from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, date, timedelta, timezone

import pytest
from sqlalchemy import text, MetaData, Table, select

import app.api.visits as visits_api
from app.models.patient import Patient
from app.models.visit import Visit
from app.models.task import Task


# ---------------------------------------------------------------------
# TEST USER (matches production contract)
# ---------------------------------------------------------------------

@dataclass
class DummyUser:
    id: uuid.UUID
    tenant_id: uuid.UUID
    role: str


# ---------------------------------------------------------------------
# SIDE EFFECT PATCHING
# ---------------------------------------------------------------------
# Dev posture:
# - RLS is OFF
# - Task engine stays REAL
# - Silence audit logging only
# ---------------------------------------------------------------------

def _patch_side_effects(monkeypatch):
    monkeypatch.setattr(visits_api, "log_event", lambda *args, **kwargs: None)


# ---------------------------------------------------------------------
# USER + TENANT HELPERS
# ---------------------------------------------------------------------

def _ensure_user_row(db_session) -> tuple[uuid.UUID, uuid.UUID]:
    """
    Ensure at least one user exists and return (user_id, tenant_id).
    Uses DB column introspection to satisfy NOT NULL columns.
    """
    row = db_session.execute(
        text("SELECT id, tenant_id FROM users LIMIT 1")
    ).first()
    if row:
        return row[0], row[1]

    md = MetaData()
    users = Table("users", md, autoload_with=db_session.bind)

    user_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    values = {"id": user_id, "tenant_id": tenant_id}

    for col in users.columns:
        if col.name in values:
            continue
        if col.primary_key or col.nullable:
            continue
        if col.default is not None or col.server_default is not None:
            continue

        try:
            py = col.type.python_type
        except Exception:
            py = None

        if py is str:
            values[col.name] = f"TEST-{col.name}-{user_id.hex[:6]}"
        elif py is bool:
            values[col.name] = True
        elif py is int:
            values[col.name] = 0
        elif py is datetime:
            values[col.name] = datetime.now(timezone.utc).replace(tzinfo=None)
        elif py is date:
            values[col.name] = date.today()

    db_session.execute(users.insert().values(**values))
    db_session.commit()
    return user_id, tenant_id


def _make_dummy_user(db_session) -> DummyUser:
    user_id, tenant_id = _ensure_user_row(db_session)
    return DummyUser(id=user_id, tenant_id=tenant_id, role="RN")


def _set_tenant_context(db_session, user: DummyUser) -> None:
    """
    Dev mode tenant context.
    RLS is OFF, so ORM context only.
    """
    db_session.info["tenant_id"] = user.tenant_id
    db_session.info["user_id"] = user.id


# ---------------------------------------------------------------------
# PATIENT / VISIT FACTORIES
# ---------------------------------------------------------------------

def _create_patient(db_session, acuity_state: str) -> Patient:
    user = _make_dummy_user(db_session)
    _set_tenant_context(db_session, user)

    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=user.tenant_id,
        mrn=f"TEST-{uuid.uuid4().hex[:10]}",
        full_name="Test Patient",
        date_of_birth=date(1950, 1, 1),
        primary_diagnosis="Test Diagnosis",
        status="ACTIVE",
        hospice_election_date=date.today(),
        acuity_state=acuity_state,
        created_by=user.id,
    )

    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)
    return patient


def _create_visit(
    db_session,
    *,
    patient_id: uuid.UUID,
    visit_type: str,
    is_supervisory: bool,
    acuity_state_at_visit: str | None,
) -> Visit:
    user = _make_dummy_user(db_session)
    _set_tenant_context(db_session, user)

    visit = Visit(
        id=uuid.uuid4(),
        tenant_id=user.tenant_id,
        patient_id=patient_id,
        provider_id=user.id,
        visit_type=visit_type.upper(),
        visit_discipline="RN",
        visit_datetime=datetime.now(timezone.utc),
        is_supervisory=is_supervisory,
        acuity_state_at_visit=acuity_state_at_visit,
        status="DRAFT",
        created_by=user.id,
    )

    db_session.add(visit)
    db_session.commit()
    db_session.refresh(visit)
    return visit


# ---------------------------------------------------------------------
# TASK QUERY HELPER
# ---------------------------------------------------------------------

def _get_poc_update_for_visit(db_session, visit_id: uuid.UUID) -> Task | None:
    """
    Deterministic lookup.
    RLS is OFF in dev, so no tenant filtering needed.
    """
    stmt = (
        select(Task)
        .where(
            Task.task_type == "POC_UPDATE",
            Task.completion_reference_type == "VISIT",
            Task.completion_reference_id == visit_id,
        )
        .order_by(Task.created_at.desc())
    )
    return db_session.execute(stmt).scalars().first()


# ---------------------------------------------------------------------
# TESTS
# ---------------------------------------------------------------------

def test_crisis_rn_finalize_creates_manual_completed_poc_update(db_session, monkeypatch):
    _patch_side_effects(monkeypatch)

    patient = _create_patient(db_session, acuity_state="CRISIS")
    visit = _create_visit(
        db_session,
        patient_id=patient.id,
        visit_type="RN",
        is_supervisory=False,
        acuity_state_at_visit="CRISIS",
    )

    user = _make_dummy_user(db_session)
    _set_tenant_context(db_session, user)

    result = visits_api.finalize_visit(
        visit_id=visit.id,
        db=db_session,
        user=user,
    )
    assert result["status"].lower() == "finalized"

    task = _get_poc_update_for_visit(db_session, visit.id)
    assert task is not None
    assert task.origin == "MANUAL"
    assert task.status == "COMPLETED"
    assert task.discipline == "RN"
    assert task.regulatory_basis == "POC_UPDATE"
    assert task.due_date == visit.visit_datetime.date()
    assert task.completion_reference_id == visit.id


def test_routine_supervisory_rn_finalize_creates_periodic_pending_poc_update(db_session, monkeypatch):
    _patch_side_effects(monkeypatch)

    patient = _create_patient(db_session, acuity_state="ROUTINE")
    visit = _create_visit(
        db_session,
        patient_id=patient.id,
        visit_type="RN",
        is_supervisory=True,
        acuity_state_at_visit="ROUTINE",
    )

    user = _make_dummy_user(db_session)
    _set_tenant_context(db_session, user)

    result = visits_api.finalize_visit(
        visit_id=visit.id,
        db=db_session,
        user=user,
    )
    assert result["status"].lower() == "finalized"

    task = _get_poc_update_for_visit(db_session, visit.id)
    assert task is not None
    assert task.origin == "PERIODIC"
    assert task.status == "PENDING"
    assert task.discipline == "RN"
    assert task.regulatory_basis == "POC_UPDATE"
    assert task.due_date == visit.visit_datetime.date() + timedelta(days=14)
    assert task.completion_reference_id == visit.id