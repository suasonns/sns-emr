from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date, timezone
from uuid import UUID
import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import text, MetaData, Table

import app.api.visits as visits_api
from app.models.patient import Patient
from app.models.visit import Visit


# =========================================================
# CANONICAL DEV TENANT (NON-NEGOTIABLE)
# =========================================================

DEV_TENANT_ID = UUID("01271980-0000-0000-0000-000005101977")


# =========================================================
# TEST USER SHAPE
# =========================================================

@dataclass
class DummyUser:
    id: uuid.UUID
    tenant_id: uuid.UUID
    role: str


# =========================================================
# SIDE EFFECT ISOLATION
# =========================================================

def _patch_side_effects(monkeypatch):
    monkeypatch.setattr(visits_api, "auto_complete_tasks_for_visit", lambda *a, **k: None)
    monkeypatch.setattr(visits_api, "log_event", lambda *a, **k: None)
    monkeypatch.setattr(visits_api, "get_current_benefit_period", lambda *a, **k: None)
    monkeypatch.setattr(visits_api, "handle_visit_finalized", lambda *a, **k: None)


# =========================================================
# DB CONTEXT HELPER (CRITICAL)
# =========================================================

def _set_db_user_context(db_session, user):
    """
    Mimics FastAPI set_tenant_context dependency.
    REQUIRED when calling endpoints directly in tests.
    """
    db_session.info["user_id"] = user.id
    db_session.info["tenant_id"] = user.tenant_id


# =========================================================
# DB HELPERS
# =========================================================

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
            values[col.name] = f"TEST-{col.name}-{uid.hex[:6]}"
        elif py is bool:
            values[col.name] = True
        elif py is int:
            values[col.name] = 0
        elif py is datetime:
            values[col.name] = datetime.now(timezone.utc).replace(tzinfo=None)
        elif py is date:
            values[col.name] = date.today()
        else:
            values[col.name] = f"TEST-{col.name}-{uid.hex[:6]}"

    db_session.execute(users.insert().values(**values))
    db_session.commit()
    return uid


def _make_dummy_user(db_session, role: str = "RN") -> DummyUser:
    user_id = _ensure_user_id(db_session)

    db_session.execute(
        text("UPDATE users SET tenant_id = :tid WHERE id = :uid"),
        {"tid": DEV_TENANT_ID, "uid": user_id},
    )
    db_session.commit()

    return DummyUser(
        id=user_id,
        tenant_id=DEV_TENANT_ID,
        role=role,
    )


# =========================================================
# ENTITY FACTORIES
# =========================================================

def _create_patient(db_session, acuity_state: str = "ROUTINE") -> Patient:
    pid = uuid.uuid4()
    user_id = _ensure_user_id(db_session)

    patient = Patient(
        id=pid,
        tenant_id=DEV_TENANT_ID,
        mrn=f"TEST-{pid.hex[:10]}",
        full_name="Test Patient",
        date_of_birth=date(1950, 1, 1),
        primary_diagnosis="Test Diagnosis",
        status="ACTIVE",
        hospice_election_date=date.today(),
        acuity_state=acuity_state,
        created_by=user_id,
    )

    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)
    return patient


def _create_visit(
    db_session,
    patient_id: uuid.UUID,
    visit_type: str,
    is_supervisory: bool,
) -> Visit:
    vid = uuid.uuid4()
    user_id = _ensure_user_id(db_session)

    # Pull acuity from patient so the visit snapshot is explicit
    patient = db_session.query(Patient).filter(Patient.id == patient_id).first()
    patient_acuity = getattr(patient, "acuity_state", None) if patient is not None else None

    vt = (visit_type or "").upper().strip()

    visit = Visit(
        id=vid,
        tenant_id=DEV_TENANT_ID,
        patient_id=patient_id,
        provider_id=user_id,

        # Visit type (RN/LVN/etc)
        visit_type=vt,

        # ✅ Discipline MUST be RN/LVN/etc (not "NURSING")
        visit_discipline=vt,

        visit_datetime=datetime.utcnow(),
        status="DRAFT",
        is_supervisory=is_supervisory,

        # ✅ Snapshot acuity explicitly so finalize logic cannot “miss” it
        acuity_state_at_visit=patient_acuity,

        created_by=user_id,
    )

    db_session.add(visit)
    db_session.commit()
    db_session.refresh(visit)
    return visit

# =========================================================
# TESTS
# =========================================================

def test_rn_routine_not_supervisory_blocked(db_session, monkeypatch):
    _patch_side_effects(monkeypatch)

    patient = _create_patient(db_session, "ROUTINE")
    visit = _create_visit(db_session, patient.id, "RN", False)
    user = _make_dummy_user(db_session, "RN")

    _set_db_user_context(db_session, user)

    with pytest.raises(HTTPException) as exc:
        visits_api.finalize_visit(visit.id, db_session, user)

    assert exc.value.status_code == 400
    assert "supervisory" in str(exc.value.detail).lower()


def test_rn_routine_supervisory_allowed(db_session, monkeypatch):
    _patch_side_effects(monkeypatch)

    patient = _create_patient(db_session, "ROUTINE")
    visit = _create_visit(db_session, patient.id, "RN", True)
    user = _make_dummy_user(db_session, "RN")

    _set_db_user_context(db_session, user)

    result = visits_api.finalize_visit(visit.id, db_session, user)
    assert result["status"].lower() == "finalized"


def test_rn_crisis_not_supervisory_allowed(db_session, monkeypatch):
    _patch_side_effects(monkeypatch)

    patient = _create_patient(db_session, "CRISIS")
    visit = _create_visit(db_session, patient.id, "RN", False)
    user = _make_dummy_user(db_session, "RN")

    _set_db_user_context(db_session, user)

    result = visits_api.finalize_visit(visit.id, db_session, user)
    assert result["status"].lower() == "finalized"


def test_non_rn_visit_allowed(db_session, monkeypatch):
    _patch_side_effects(monkeypatch)

    patient = _create_patient(db_session, "ROUTINE")
    visit = _create_visit(db_session, patient.id, "LVN", False)
    user = _make_dummy_user(db_session, "RN")

    _set_db_user_context(db_session, user)

    result = visits_api.finalize_visit(visit.id, db_session, user)
    assert result["status"].lower() == "finalized"