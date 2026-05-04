from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date, timedelta
import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import text, MetaData, Table
from sqlalchemy.orm import Session

import app.api.visits as visits_api

from app.models.patient import Patient
from app.models.visit import Visit
from app.models.task import Task


@dataclass
class DummyUser:
    user_id: uuid.UUID
    role: str


def _patch_side_effects(monkeypatch):
    """
    Tests the inline POC_UPDATE automation in finalize_visit().
    Patch audit and unrelated task completion only.
    """
    monkeypatch.setattr(visits_api, "auto_complete_tasks_for_visit", lambda *args, **kwargs: None)
    monkeypatch.setattr(visits_api, "log_event", lambda *args, **kwargs: None)


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
            values[col.name] = datetime.utcnow()
        elif py is date:
            values[col.name] = date.today()
        else:
            values[col.name] = f"TEST-{col.name}-{uid.hex[:6]}"

    db_session.execute(users.insert().values(**values))
    db_session.commit()
    return uid


def _fill_required_fields(model_cls, overrides: dict) -> dict:
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
            values[col.name] = datetime.utcnow()
        elif py is date:
            values[col.name] = date.today()
        else:
            enums = getattr(getattr(col.type, "enums", None), "__iter__", None)
            if enums:
                values[col.name] = list(col.type.enums)[0]
            else:
                values[col.name] = f"TEST-{col.name}"

    return values


def _create_patient(db_session, acuity_state: str) -> Patient:
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
    acuity_state_at_visit: str,
) -> Visit:
    vid = uuid.uuid4()
    user_id = _ensure_user_id(db_session)
    now = datetime.utcnow()

    base = {
        "id": vid,
        "patient_id": patient_id,
        "provider_id": user_id,
        "visit_type": visit_type.upper(),
        "visit_datetime": now,
        "status": "draft",
        "is_supervisory": is_supervisory,
        "created_by": user_id,
        "acuity_state_at_visit": acuity_state_at_visit.upper(),
    }

    values = _fill_required_fields(Visit, base)
    v = Visit(**values)

    db_session.add(v)
    db_session.commit()
    db_session.refresh(v)
    return v


def _get_poc_update_for_visit(db_session, visit_id: uuid.UUID) -> Task | None:
    return (
        db_session.query(Task)
        .filter(
            Task.task_type == "POC_UPDATE",
            Task.completion_reference_type == "VISIT",
            Task.completion_reference_id == str(visit_id),  # VARCHAR in DB
        )
        .order_by(Task.created_at.desc())
        .first()
    )


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

    user = DummyUser(user_id=_ensure_user_id(db_session), role="RN")

    result = visits_api.finalize_visit(visit_id=visit.id, db=db_session, user=user)
    assert result["status"].lower() == "finalized"

    task = _get_poc_update_for_visit(db_session, visit.id)
    assert task is not None
    assert task.origin == "MANUAL"
    assert task.status == "COMPLETED"
    assert task.discipline == "RN"
    assert task.regulatory_basis == "POC_UPDATE"
    assert task.due_date == visit.visit_datetime.date()
    assert task.completion_reference_id == str(visit.id)


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

    user = DummyUser(user_id=_ensure_user_id(db_session), role="RN")

    result = visits_api.finalize_visit(visit_id=visit.id, db=db_session, user=user)
    assert result["status"].lower() == "finalized"

    task = _get_poc_update_for_visit(db_session, visit.id)
    assert task is not None
    assert task.origin == "PERIODIC"
    assert task.status == "PENDING"
    assert task.discipline == "RN"
    assert task.regulatory_basis == "POC_UPDATE"
    assert task.due_date == (visit.visit_datetime.date() + timedelta(days=14))
    assert task.completion_reference_id == str(visit.id)