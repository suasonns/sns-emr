# tests/test_poc_update_task_compliance.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date, timedelta
from uuid import UUID
import uuid

import pytest
from sqlalchemy import text, MetaData, Table

import app.api.visits as visits_api
from app.models.patient import Patient
from app.models.visit import Visit
from app.models.task import Task


# =========================================================
# CANONICAL DEV TENANT (NON-NEGOTIABLE)
# =========================================================

DEV_TENANT_ID = UUID("01271980-0000-0000-0000-000005101977")


# =========================================================
# USER SHAPE (MATCHES get_current_user CONTRACT)
# =========================================================

@dataclass
class DummyUser:
    id: uuid.UUID
    tenant_id: uuid.UUID
    role: str


# =========================================================
# PATCH SIDE EFFECTS (DO NOT PATCH task engine!)
# =========================================================

def _patch_side_effects(monkeypatch):
    # Keep task engine active (we are testing it).
    # Patch only things that add noise or rely on other subsystems.

    if hasattr(visits_api, "auto_complete_tasks_for_visit"):
        monkeypatch.setattr(visits_api, "auto_complete_tasks_for_visit", lambda *a, **k: None)

    if hasattr(visits_api, "log_event"):
        monkeypatch.setattr(visits_api, "log_event", lambda *a, **k: None)

    # Make benefit period lookup harmless (we allow benefit_period_id=None)
    if hasattr(visits_api, "get_current_benefit_period"):
        monkeypatch.setattr(visits_api, "get_current_benefit_period", lambda *a, **k: None)


# =========================================================
# DB CONTEXT (MIMIC FastAPI dependency injection)
# =========================================================

def _set_db_user_context(db_session, user: DummyUser):
    db_session.info["user_id"] = user.id
    db_session.info["tenant_id"] = user.tenant_id


# =========================================================
# DB HELPERS (SAFE SEEDING)
# =========================================================

def _ensure_tenant_exists(db_session, tenant_id: UUID):
    """
    Ensures the tenant row exists WITHOUT creating random tenants.
    If tenants table has required fields, we fill them safely using reflection.
    """
    row = db_session.execute(
        text("SELECT id FROM tenants WHERE id = :tid"),
        {"tid": tenant_id},
    ).first()
    if row:
        return

    md = MetaData()
    tenants = Table("tenants", md, autoload_with=db_session.bind)

    values = {"id": tenant_id}

    for col in tenants.columns:
        if col.name in values:
            continue
        if col.primary_key or col.nullable:
            continue
        if col.default is not None or col.server_default is not None:
            continue

        # Minimal safe values for required columns
        if "name" in col.name:
            values[col.name] = "DEV_TENANT_REAL"
        elif "code" in col.name:
            values[col.name] = "DEV_REAL"
        elif "created" in col.name or "updated" in col.name:
            values[col.name] = datetime.utcnow()
        else:
            # Generic safe fallback
            try:
                py = col.type.python_type
            except Exception:
                py = None

            if py is str:
                values[col.name] = f"DEV_{col.name}".upper()
            elif py is bool:
                values[col.name] = True
            elif py is int:
                values[col.name] = 0
            elif py is uuid.UUID:
                values[col.name] = uuid.uuid4()
            elif py is datetime:
                values[col.name] = datetime.utcnow()
            elif py is date:
                values[col.name] = date.today()
            else:
                values[col.name] = f"DEV_{col.name}".upper()

    db_session.execute(tenants.insert().values(**values))
    db_session.commit()


def _ensure_user_id(db_session) -> uuid.UUID:
    row = db_session.execute(text("SELECT id FROM users LIMIT 1")).first()
    if row:
        return row[0]

    md = MetaData()
    users = Table("users", md, autoload_with=db_session.bind)

    uid = uuid.uuid4()
    values = {"id": uid}

    for col in users.columns:
        if col.name in values or col.nullable or col.primary_key:
            continue
        if col.default is not None or col.server_default is not None:
            continue

        try:
            py = col.type.python_type
        except Exception:
            py = None

        if py is uuid.UUID:
            values[col.name] = uuid.uuid4()
        elif py is str:
            if "email" in col.name:
                values[col.name] = f"test-{uid.hex[:8]}@example.com"
            else:
                values[col.name] = f"TEST-{col.name}-{uid.hex[:6]}"
        elif py is bool:
            values[col.name] = True
        elif py is int:
            values[col.name] = 0
        elif py is datetime:
            values[col.name] = datetime.utcnow()
        elif py is date:
            values[col.name] = date.today()
        else:
            values[col.name] = f"TEST-{col.name}-{uid.hex[:6]}"

    db_session.execute(users.insert().values(**values))
    db_session.commit()
    return uid


def _make_dummy_user(db_session, role: str = "RN") -> DummyUser:
    """
    Returns a user with canonical tenant id.
    """
    _ensure_tenant_exists(db_session, DEV_TENANT_ID)

    user_id = _ensure_user_id(db_session)

    # Best effort: if users table has tenant_id, align it.
    try:
        db_session.execute(
            text("UPDATE users SET tenant_id = :tid WHERE id = :uid"),
            {"tid": DEV_TENANT_ID, "uid": user_id},
        )
        db_session.commit()
    except Exception:
        db_session.rollback()

    return DummyUser(id=user_id, tenant_id=DEV_TENANT_ID, role=role)


# =========================================================
# ENTITY FACTORIES
# =========================================================

def _create_patient(db_session, acuity_state: str) -> Patient:
    _ensure_tenant_exists(db_session, DEV_TENANT_ID)
    user_id = _ensure_user_id(db_session)

    pid = uuid.uuid4()

    patient = Patient(
        id=pid,
        tenant_id=DEV_TENANT_ID,
        mrn=f"TEST-{pid.hex[:10]}",
        full_name="Test Patient",
        date_of_birth=date(1950, 1, 1),
        primary_diagnosis="TEST DX",
        status="ACTIVE",
        hospice_election_date=date.today(),
        acuity_state=acuity_state,
        created_by=user_id,
    )

    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)
    return patient


def _create_visit(db_session, patient_id: uuid.UUID, acuity: str, is_supervisory: bool) -> Visit:
    user_id = _ensure_user_id(db_session)
    vid = uuid.uuid4()

    # Use a fixed visit datetime for predictable due_date math
    visit_dt = datetime(2026, 5, 29, 9, 0, 0)

    visit = Visit(
        id=vid,
        tenant_id=DEV_TENANT_ID,
        patient_id=patient_id,
        provider_id=user_id,
        visit_type="RN",
        visit_discipline="RN",
        status="DRAFT",
        visit_datetime=visit_dt,
        is_supervisory=is_supervisory,
        acuity_state_at_visit=acuity,
        created_by=user_id,
    )

    db_session.add(visit)
    db_session.commit()
    db_session.refresh(visit)
    return visit


def _fetch_poc_tasks_for_visit(db_session, visit_id: uuid.UUID):
    """
    Return all POC_UPDATE tasks anchored to this visit (evidence linkage).
    """
    return (
        db_session.query(Task)
        .filter(
            Task.task_type == "POC_UPDATE",
            Task.completion_reference_type == "VISIT",
            Task.completion_reference_id == visit_id,
        )
        .all()
    )


# =========================================================
# TESTS (SURVEY-DEFENSIBLE PROOF)
# =========================================================

def test_crisis_rn_finalize_creates_same_day_completed_poc_update(db_session, monkeypatch):
    """
    CRISIS RULE:
    - Finalized RN visit creates POC_UPDATE
    - status = COMPLETED
    - origin = MANUAL
    - due_date = visit_day
    - completed_at populated
    - evidence linked to VISIT(visit.id)
    - no duplicates on repeat finalize
    """
    _patch_side_effects(monkeypatch)

    patient = _create_patient(db_session, acuity_state="CRISIS")
    visit = _create_visit(db_session, patient_id=patient.id, acuity="CRISIS", is_supervisory=False)
    user = _make_dummy_user(db_session, role="RN")
    _set_db_user_context(db_session, user)

    result = visits_api.finalize_visit(visit_id=visit.id, db=db_session, user=user)
    assert result["status"].lower() in ("finalized", "already_finalized")

    tasks = _fetch_poc_tasks_for_visit(db_session, visit.id)
    assert len(tasks) == 1

    t = tasks[0]
    assert str(t.tenant_id) == str(DEV_TENANT_ID)
    assert t.status == "COMPLETED"
    assert t.origin == "MANUAL"
    assert t.due_date == visit.visit_datetime.date()
    assert t.completed_at is not None
    assert t.completion_reference_type == "VISIT"
    assert str(t.completion_reference_id) == str(visit.id)

    # Idempotency: run finalize again; still only one task
    result2 = visits_api.finalize_visit(visit_id=visit.id, db=db_session, user=user)
    assert result2["status"].lower() in ("finalized", "already_finalized")

    tasks2 = _fetch_poc_tasks_for_visit(db_session, visit.id)
    assert len(tasks2) == 1


def test_routine_supervisory_rn_finalize_creates_pending_poc_update_due_plus_14(db_session, monkeypatch):
    """
    ROUTINE RULE:
    - Finalized RN supervisory visit creates next POC_UPDATE
    - status = PENDING
    - origin = PERIODIC
    - due_date = visit_day + 14 days
    - completed_at is NULL
    - evidence linked to VISIT(visit.id)
    - no duplicates on repeat finalize
    """
    _patch_side_effects(monkeypatch)

    patient = _create_patient(db_session, acuity_state="ROUTINE")
    visit = _create_visit(db_session, patient_id=patient.id, acuity="ROUTINE", is_supervisory=True)
    user = _make_dummy_user(db_session, role="RN")
    _set_db_user_context(db_session, user)

    result = visits_api.finalize_visit(visit_id=visit.id, db=db_session, user=user)
    assert result["status"].lower() in ("finalized", "already_finalized")

    tasks = _fetch_poc_tasks_for_visit(db_session, visit.id)
    assert len(tasks) == 1

    t = tasks[0]
    assert str(t.tenant_id) == str(DEV_TENANT_ID)
    assert t.status == "PENDING"
    assert t.origin == "PERIODIC"
    assert t.due_date == (visit.visit_datetime.date() + timedelta(days=14))
    assert t.completed_at is None
    assert t.completion_reference_type == "VISIT"
    assert str(t.completion_reference_id) == str(visit.id)

    # Idempotency: finalize again; still one task
    result2 = visits_api.finalize_visit(visit_id=visit.id, db=db_session, user=user)
    assert result2["status"].lower() in ("finalized", "already_finalized")

    tasks2 = _fetch_poc_tasks_for_visit(db_session, visit.id)
    assert len(tasks2) == 1