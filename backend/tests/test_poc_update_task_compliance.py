from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date
from uuid import UUID
import uuid

import pytest
from sqlalchemy import text

import app.api.visits as visits_api
from app.models.patient import Patient
from app.models.visit import Visit
from app.models.task import Task


DEV_TENANT_ID = UUID("01271980-0000-0000-0000-000005101977")


@dataclass
class DummyUser:
    id: uuid.UUID
    tenant_id: uuid.UUID
    role: str


def _ensure_user_id(db_session):
    row = db_session.execute(text("SELECT id FROM users LIMIT 1")).first()
    return row[0]


def _create_patient(db_session, acuity_state: str) -> Patient:
    user_id = _ensure_user_id(db_session)

    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=DEV_TENANT_ID,
        mrn=f"TEST-{uuid.uuid4().hex[:10]}",
        full_name="Test Patient",
        date_of_birth=date(1950, 1, 1),
        primary_diagnosis="TEST DX",
        status="ACTIVE",
        admission_status="PRE_REFERRAL",
        hospice_election_date=date.today(),
        acuity_state=acuity_state,
        created_by=user_id,
    )

    db_session.add(patient)
    db_session.commit()
    return patient


def _create_visit(db_session, patient_id: UUID, acuity: str, is_supervisory: bool) -> Visit:
    user_id = _ensure_user_id(db_session)

    visit = Visit(
        id=uuid.uuid4(),
        tenant_id=DEV_TENANT_ID,
        patient_id=patient_id,
        provider_id=user_id,
        visit_type="RN",
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