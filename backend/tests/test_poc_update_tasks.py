from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date
import uuid

import pytest
from sqlalchemy import text, select

import app.api.visits as visits_api
from app.models.patient import Patient
from app.models.visit import Visit
from app.models.task import Task


@dataclass
class DummyUser:
    id: uuid.UUID
    tenant_id: uuid.UUID
    role: str


def _ensure_user(db_session):
    row = db_session.execute(text("SELECT id, tenant_id FROM users LIMIT 1")).first()
    return row[0], row[1]


def _create_patient(db_session, acuity_state: str):
    user_id, tenant_id = _ensure_user(db_session)

    p = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"TEST-{uuid.uuid4().hex[:10]}",
        full_name="Test Patient",
        date_of_birth=date(1950, 1, 1),
        primary_diagnosis="Test Diagnosis",
        status="ACTIVE",
        admission_status="PRE_REFERRAL",
        hospice_election_date=date.today(),
        acuity_state=acuity_state,
        created_by=user_id,
    )

    db_session.add(p)
    db_session.commit()
    return p


def _create_visit(db_session, patient_id, visit_type, is_supervisory, acuity):
    user_id, tenant_id = _ensure_user(db_session)

    visit = Visit(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        provider_id=user_id,
        visit_type=visit_type,
        visit_discipline="RN",
        visit_datetime=datetime.utcnow(),
        status="DRAFT",
        is_supervisory=is_supervisory,
        acuity_state_at_visit=acuity,
        created_by=user_id,
    )

    db_session.add(visit)
    db_session.commit()
    return visit