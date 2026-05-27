from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date, timezone
import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import text, MetaData, Table, inspect

import app.api.visits as visits_api

from app.models.patient import Patient
from app.models.visit import Visit


@dataclass
class DummyUser:
    id: uuid.UUID
    tenant_id: uuid.UUID
    role: str


def _patch_side_effects(monkeypatch):
    if hasattr(visits_api, "auto_complete_tasks_for_visit"):
        monkeypatch.setattr(
            visits_api,
            "auto_complete_tasks_for_visit",
            lambda *args, **kwargs: None,
        )

    if hasattr(visits_api, "log_event"):
        monkeypatch.setattr(
            visits_api,
            "log_event",
            lambda *args, **kwargs: None,
        )

    # ✅ Stub benefit period lookup (signature drift isolation)
    if hasattr(visits_api, "get_current_benefit_period"):
        monkeypatch.setattr(
            visits_api,
            "get_current_benefit_period",
            lambda *args, **kwargs: None,
        )

    # ✅ Stub task engine finalize hook (signature drift isolation)
    if hasattr(visits_api, "handle_visit_finalized"):
        monkeypatch.setattr(
            visits_api,
            "handle_visit_finalized",
            lambda *args, **kwargs: None,
        )

    # ✅ IMPORTANT: Stub benefit period lookup to isolate RN guardrail logic
    if hasattr(visits_api, "get_current_benefit_period"):
        monkeypatch.setattr(
            visits_api,
            "get_current_benefit_period",
            lambda *args, **kwargs: None,
        )

def _db_varchar_len(db_session, table_name: str, col_name: str):
    """
    Reflect real DB column definitions to survive SQLAlchemy model/schema drift.
    Returns varchar length if available, else None.
    """
    insp = inspect(db_session.bind)
    for c in insp.get_columns(table_name):
        if c.get("name") == col_name:
            t = c.get("type")
            return getattr(t, "length", None)
    return None


def _truncate_for_model_col(db_session, model_cls, col, value):
    """
    Enterprise-grade safety:
    1) Truncate using SQLAlchemy model column length if present.
    2) Fallback to DB-reflected varchar length if model has no length.
    """
    if value is None or not isinstance(value, str):
        return value

    length = getattr(col.type, "length", None)
    if not length:
        length = _db_varchar_len(db_session, model_cls.__table__.name, col.name)

    if length and len(value) > length:
        return value[:length]
    return value


def _truncate_for_table_col(col, value):
    """
    For reflected Table() objects (autoload_with), col.type.length usually matches DB.
    """
    if value is None or not isinstance(value, str):
        return value

    length = getattr(col.type, "length", None)
    if length and len(value) > length:
        return value[:length]
    return value


def _ensure_user_id(db_session) -> uuid.UUID:
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
                v = f"test-{uid.hex[:8]}@example.com"
            elif "username" in col.name:
                v = f"test_{uid.hex[:8]}"
            else:
                v = f"TEST-{col.name}-{uid.hex[:6]}"
            values[col.name] = _truncate_for_table_col(col, v)
        elif py is bool:
            values[col.name] = True
        elif py is int:
            values[col.name] = 0
        elif py is datetime:
            values[col.name] = datetime.now(timezone.utc).replace(tzinfo=None)
        elif py is date:
            values[col.name] = date.today()
        else:
            v = f"TEST-{col.name}-{uid.hex[:6]}"
            values[col.name] = _truncate_for_table_col(col, v)

    db_session.execute(users.insert().values(**values))
    db_session.commit()
    return uid


def _make_dummy_user(db_session, role: str = "RN") -> DummyUser:
    """
    Enterprise-grade test user matching the production get_current_user contract:
      - user.id
      - user.tenant_id
      - user.role
    """
    user_id = _ensure_user_id(db_session)

    # Try to get tenant_id from users table (common multi-tenant pattern)
    row = db_session.execute(
        text("SELECT tenant_id FROM users WHERE id = :uid"),
        {"uid": user_id},
    ).first()

    tenant_id = row[0] if row and row[0] is not None else None

    # Safety fallback: if tenant_id is missing, assign one and persist it.
    # (This avoids None blowing up benefit period lookups in finalize_visit.)
    if tenant_id is None:
        tenant_id = uuid.uuid4()
        try:
            db_session.execute(
                text("UPDATE users SET tenant_id = :tid WHERE id = :uid"),
                {"tid": tenant_id, "uid": user_id},
            )
            db_session.commit()
        except Exception:
            # If users table does not have tenant_id or update is blocked,
            # we still return a deterministic UUID for tenant scoping in tests.
            db_session.rollback()

    return DummyUser(id=user_id, tenant_id=tenant_id, role=role)


def _fill_required_fields(db_session, model_cls, overrides: dict) -> dict:
    """
    Populate all required (NOT NULL, no default) fields with safe test values,
    enforcing varchar lengths even if SQLAlchemy models drift from DB schema.
    """
    values = dict(overrides)
    table = model_cls.__table__

    for col in table.columns:
        if col.name in values:
            values[col.name] = _truncate_for_model_col(db_session, model_cls, col, values[col.name])
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
            v = f"TEST-{col.name}"
            values[col.name] = _truncate_for_model_col(db_session, model_cls, col, v)
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
            if getattr(col.type, "enums", None):
                values[col.name] = list(col.type.enums)[0]
            else:
                v = f"TEST-{col.name}"
                values[col.name] = _truncate_for_model_col(db_session, model_cls, col, v)

    return values


def _create_patient(db_session, acuity_state: str = "ROUTINE") -> Patient:
    pid = uuid.uuid4()
    user_id = _ensure_user_id(db_session)

    base = {
        "id": pid,
        "mrn": f"TEST-{pid.hex[:10]}",
        "full_name": "Test Patient",
        "date_of_birth": date(1950, 1, 1),
        "primary_diagnosis": "Test Diagnosis",
        "status": "ACTIVE",  # DB enum often requires uppercase
        "hospice_election_date": date.today(),
        "acuity_state": acuity_state,
        "created_by": user_id,
    }

    values = _fill_required_fields(db_session, Patient, base)
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
    vid = uuid.uuid4()
    user_id = _ensure_user_id(db_session)

    # Align tenant + acuity snapshot with patient (enterprise-grade / survey-defensible)
    patient = db_session.query(Patient).filter(Patient.id == patient_id).first()
    patient_tenant_id = getattr(patient, "tenant_id", None) if patient is not None else None
    patient_acuity = getattr(patient, "acuity_state", None) if patient is not None else None

    base = {
        "id": vid,
        "patient_id": patient_id,
        "provider_id": user_id,
        "visit_type": (visit_type or "").upper(),
        "visit_discipline": "NURSING",  # <= 16 chars (DB varchar(16))
        "visit_datetime": datetime.utcnow(),
        "status": "DRAFT",
        "is_supervisory": is_supervisory,
        "created_by": user_id,

        # ✅ IMPORTANT: snapshot acuity at the time of visit (guardrails depend on this)
        "acuity_state_at_visit": patient_acuity,
    }

    # If Visit has tenant_id and we know the patient's tenant_id, keep them consistent
    if "tenant_id" in Visit.__table__.columns and patient_tenant_id is not None:
        base["tenant_id"] = patient_tenant_id

    values = _fill_required_fields(db_session, Visit, base)
    v = Visit(**values)
    db_session.add(v)
    db_session.commit()
    db_session.refresh(v)
    return v

def test_rn_routine_not_supervisory_blocked(db_session, monkeypatch):
    _patch_side_effects(monkeypatch)

    patient = _create_patient(db_session, acuity_state="ROUTINE")
    visit = _create_visit(db_session, patient_id=patient.id, visit_type="RN", is_supervisory=False)
    user = _make_dummy_user(db_session, role="RN")

    with pytest.raises(HTTPException) as exc:
        visits_api.finalize_visit(visit_id=visit.id, db=db_session, user=user)

    assert exc.value.status_code == 400
    assert "explicitly marked as supervisory" in str(exc.value.detail)


def test_rn_routine_supervisory_allowed(db_session, monkeypatch):
    _patch_side_effects(monkeypatch)

    patient = _create_patient(db_session, acuity_state="ROUTINE")
    visit = _create_visit(db_session, patient_id=patient.id, visit_type="RN", is_supervisory=True)
    user = _make_dummy_user(db_session, role="RN")

    result = visits_api.finalize_visit(visit_id=visit.id, db=db_session, user=user)

    assert isinstance(result, dict)
    assert result["visit_id"] == str(visit.id)
    assert result["status"].lower() == "finalized"

    refreshed = db_session.query(Visit).filter(Visit.id == visit.id).first()
    assert refreshed is not None
    assert refreshed.finalized_at is not None


def test_rn_crisis_not_supervisory_allowed(db_session, monkeypatch):
    _patch_side_effects(monkeypatch)

    patient = _create_patient(db_session, acuity_state="CRISIS")
    visit = _create_visit(db_session, patient_id=patient.id, visit_type="RN", is_supervisory=False)
    user = _make_dummy_user(db_session, role="RN")

    result = visits_api.finalize_visit(visit_id=visit.id, db=db_session, user=user)

    assert isinstance(result, dict)
    assert result["visit_id"] == str(visit.id)
    assert result["status"].lower() == "finalized"

    refreshed = db_session.query(Visit).filter(Visit.id == visit.id).first()
    assert refreshed is not None
    assert refreshed.finalized_at is not None


def test_non_rn_visit_allowed(db_session, monkeypatch):
    _patch_side_effects(monkeypatch)

    patient = _create_patient(db_session, acuity_state="ROUTINE")
    visit = _create_visit(db_session, patient_id=patient.id, visit_type="LVN", is_supervisory=False)
    user = _make_dummy_user(db_session, role="RN")

    result = visits_api.finalize_visit(visit_id=visit.id, db=db_session, user=user)

    assert isinstance(result, dict)
    assert result["visit_id"] == str(visit.id)
    assert result["status"].lower() == "finalized"