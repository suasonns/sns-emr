from __future__ import annotations

import os
from datetime import datetime, date
import uuid

from sqlalchemy import text
from app.models.patient import Patient


TEST_TENANT_ID = uuid.UUID(os.getenv("REAL_TENANT_ID", "01271980-0000-0000-0000-000005101977"))


def _ensure_user_id(db_session):
    row = db_session.execute(text("SELECT id FROM users LIMIT 1")).first()
    return row[0]


def _create_patient(db_session, acuity_state: str):
    user_id = _ensure_user_id(db_session)

    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=TEST_TENANT_ID,
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

    db_session.add(patient)
    db_session.commit()
    return patient