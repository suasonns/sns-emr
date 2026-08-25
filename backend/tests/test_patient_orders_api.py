from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.models.admission import Admission
from app.models.patient import Patient
from app.models.patient_order import PatientOrder


def _make_patient_and_admission(db_session, tenant_id):
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"PORD-{uuid.uuid4().hex[:12]}",
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="Hospice qualifying diagnosis",
        status="ACTIVE",
        admission_status="PRE_REFERRAL",
        created_by=None,
    )
    db_session.add(patient)
    db_session.commit()

    admission = Admission(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient.id,
        status="ACTIVE",
    )
    db_session.add(admission)
    db_session.commit()

    return patient, admission


@pytest.mark.integration
def test_add_order_creates_manual_order(client, db_session, rn_headers):
    """Regression test: add_order previously referenced an undefined
    `order_type` local variable (should have been `payload.order_type`),
    so every call raised NameError/500. Confirms the fixed endpoint works
    and defaults source_kind to MANUAL."""
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)

    resp = client.post(
        f"/patient-orders/patients/{patient.id}",
        json={"order_type": "dme", "order_text": "Hospital bed"},
        headers=rn_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["order_type"] == "DME"
    assert body["order_text"] == "Hospital bed"

    order = db_session.query(PatientOrder).filter(PatientOrder.patient_id == patient.id).first()
    assert order is not None
    assert order.source_kind == "MANUAL"


@pytest.mark.integration
def test_add_order_rejects_invalid_order_type(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)

    resp = client.post(
        f"/patient-orders/patients/{patient.id}",
        json={"order_type": "NOT_A_TYPE", "order_text": "Something"},
        headers=rn_headers,
    )
    assert resp.status_code == 422
