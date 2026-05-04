from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date, timezone
import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import text, MetaData, Table

# IMPORTANT: must match your actual module path that contains finalize_visit()
import app.api.visits as visits_api

from app.models.patient import Patient
from app.models.visit import Visit


# ----------------------------
# Minimal user object
# ----------------------------
@dataclass
class DummyUser:
    user_id: uuid.UUID
    role: str


# ----------------------------
# Helpers
# ----------------------------
def _patch_side_effects(monkeypatch):
    """
    These tests are about the RN guardrail ONLY.
    Patch side effects so failures don't come from unrelated audit/task code.

    NOTE: handle_poc_update_for_visit was removed/disabled in visits.py.
    Patch only what exists.
    """
    if hasattr(visits_api, "auto_complete_tasks_for_visit"):
        monkeypatch.setattr(visits_api, "auto_complete_tasks_for_visit", lambda *args, **kwargs: None)
    if hasattr(visits_api, "log_event"):
        monkeypatch.setattr(visits_api, "log_event", lambda *args, **kwargs: None)


def _ensure_user_id(db_session) -> uuid.UUID:
    """
    Return an existing users.id if present.
    If none exist, insert a minimal user row satisfying NOT NULL constraints.
    Keeps FK fields like created_by/provider_id valid.
    """
    row = db_session.execute(text("SELECT id FROM users LIMIT 1")).first()
    if row:
        return row[0]

    md = MetaData()
    users = Table("users", md, autoload_with=db_session.bind)

    uid = uuid.uuid4()
    values = {"id": uid}

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

        if py is uuid.UUID:
            values[col.name] = uuid.uuid4()
        elif py is str:
            if "email" in col.name:
                values[col.name] = f"test-{uid.hex[:8]}@example.com"
            elif "username" in col.name:
                values[col.name] = f"test_{uid.hex[:8]}"
            else:
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


def _fill_required_fields(model_cls, overrides: dict) -> dict:
    """
    Fill required (NOT NULL) fields for a SQLAlchemy model using introspection.
    """
    values = dict(overrides)
    table = model_cls.__table__

    for col in table.columns:
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

        if py is uuid.UUID:
            values[col.name] = uuid.uuid4()
        elif py is str:
            values[col.name] = f"TEST-{col.name}"
        elif py is bool:
            values[col.name] = False
        elif py is int:
            values[col.name] = 0
        elif py is float:
            values[col.name] = 0.0
        elif py is datetime:
            values[col.name] = datetime.now(timezone.utc).replace(tzinfo=None)
        elif py is date:
            values[col.name] = date.today()
        else:
            enums = getattr(getattr(col.type, "enums", None), "__iter__", None)
            if enums:
                values[col.name] = list(col.type.enums)[0]
            else:
                values[col.name] = f"TEST-{col.name}"

    return values


def _create_patient(db_session, acuity_state: str = "ROUTINE") -> Patient:
    """
    Create a Patient row satisfying NOT NULL constraints + FK constraints.
    """
    pid = uuid.uuid4()
    user_id = _ensure_user_id(db_session)

    base = {
        "id": pid,
        "mrn": f"TEST-{pid.hex[:10]}",
        "full_name": "Test Patient",
        "date_of_birth": date(1950, 1, 1),
        "primary_diagnosis": "Test Diagnosis",
        "status": "active",
        "hospice_election_date": date.today(),
        "acuity_state": acuity_state,
        "created_by": user_id,
    }

    values = _fill_required_fields(Patient, base)
    p = Patient(**values)
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


def _create_visit(
    db_session,
    patient_id: uuid.UUID,
    visit_type: str,
    is_supervisory: bool,
) -> Visit:
    """
    Create a Visit row aligned to your actual visits schema.
    """
    vid = uuid.uuid4()
    user_id = _ensure_user_id(db_session)

    base = {
        "id": vid,
        "patient_id": patient_id,
        "provider_id": user_id,
        "visit_type": (visit_type or "").upper(),
        "visit_datetime": datetime.utcnow(),
        "status": "draft",
        "is_supervisory": is_supervisory,
        "created_by": user_id,
    }

    values = _fill_required_fields(Visit, base)
    v = Visit(**values)
    db_session.add(v)
    db_session.commit()
    db_session.refresh(v)
    return v


# ----------------------------
# Tests
# ----------------------------
def test_rn_routine_not_supervisory_blocked(db_session, monkeypatch):
    """
    RN + ROUTINE + not supervisory => must BLOCK finalization.
    """
    _patch_side_effects(monkeypatch)

    patient = _create_patient(db_session, acuity_state="ROUTINE")
    visit = _create_visit(db_session, patient_id=patient.id, visit_type="RN", is_supervisory=False)
    user = DummyUser(user_id=_ensure_user_id(db_session), role="RN")

    with pytest.raises(HTTPException) as exc:
        visits_api.finalize_visit(visit_id=visit.id, db=db_session, user=user)

    assert exc.value.status_code == 400
    assert "explicitly marked as supervisory" in str(exc.value.detail)


def test_rn_routine_supervisory_allowed(db_session, monkeypatch):
    """
    RN + ROUTINE + supervisory => must ALLOW finalization.
    """
    _patch_side_effects(monkeypatch)

    patient = _create_patient(db_session, acuity_state="ROUTINE")
    visit = _create_visit(db_session, patient_id=patient.id, visit_type="RN", is_supervisory=True)
    user = DummyUser(user_id=_ensure_user_id(db_session), role="RN")

    result = visits_api.finalize_visit(visit_id=visit.id, db=db_session, user=user)

    assert isinstance(result, dict)
    assert result["visit_id"] == str(visit.id)
    assert result["status"].lower() == "finalized"

    refreshed = db_session.query(Visit).filter(Visit.id == visit.id).first()
    assert refreshed is not None
    assert refreshed.finalized_at is not None


def test_rn_crisis_not_supervisory_allowed(db_session, monkeypatch):
    """
    RN + CRISIS + not supervisory => must ALLOW finalization (crisis exemption).
    """
    _patch_side_effects(monkeypatch)

    patient = _create_patient(db_session, acuity_state="CRISIS")
    visit = _create_visit(db_session, patient_id=patient.id, visit_type="RN", is_supervisory=False)
    user = DummyUser(user_id=_ensure_user_id(db_session), role="RN")

    result = visits_api.finalize_visit(visit_id=visit.id, db=db_session, user=user)

    assert isinstance(result, dict)
    assert result["visit_id"] == str(visit.id)
    assert result["status"].lower() == "finalized"

    refreshed = db_session.query(Visit).filter(Visit.id == visit.id).first()
    assert refreshed is not None
    assert refreshed.finalized_at is not None


def test_non_rn_visit_allowed(db_session, monkeypatch):
    """
    Non-RN visits are not subject to RN supervisory guardrail.
    """
    _patch_side_effects(monkeypatch)

    patient = _create_patient(db_session, acuity_state="ROUTINE")
    visit = _create_visit(db_session, patient_id=patient.id, visit_type="LVN", is_supervisory=False)
    user = DummyUser(user_id=_ensure_user_id(db_session), role="RN")

    result = visits_api.finalize_visit(visit_id=visit.id, db=db_session, user=user)

    assert isinstance(result, dict)
    assert result["visit_id"] == str(visit.id)
    assert result["status"].lower() == "finalized"