from __future__ import annotations

import pytest

from app.models.patient import Patient
from app.models.patient_facesheet import PatientFaceSheet
from app.models.admission import Admission


@pytest.mark.integration
def test_create_patient_from_referral_creates_full_intake_record(client, db_session, rn_headers):
    """Regression coverage for the referral-intake endpoint. This endpoint
    already existed with zero test coverage and zero frontend caller before
    the "Add New Patient" UI (PatientCensus.jsx -> ReferralIntakeModal) was
    wired to it -- confirms it still creates patient + face sheet + primary
    diagnosis + admission from a single referral payload."""
    payload = {
        "first_name": "Referral",
        "last_name": "Intake",
        "date_of_birth": "1945-03-02",
        "phone": "555-010-2020",
        "referral_source": "Memorial Hospital",
        "referral_date": "2026-08-20",
        "primary_diagnosis": "Diagnosis pending",
        "attending_physician_name": "Dr. Alex Rivera",
    }

    resp = client.post("/patients/from-referral", json=payload, headers=rn_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["facesheet_created"] is True
    assert body["admission_status"] == "REFERRAL"

    patient = db_session.query(Patient).filter(Patient.id == body["id"]).first()
    assert patient is not None
    assert patient.admission_status == "REFERRAL"

    facesheet = db_session.query(PatientFaceSheet).filter(PatientFaceSheet.patient_id == patient.id).first()
    assert facesheet is not None
    assert facesheet.first_name == "Referral"
    assert facesheet.last_name == "Intake"

    admission = db_session.query(Admission).filter(Admission.patient_id == patient.id).first()
    assert admission is not None
    assert admission.status == "PENDING"


@pytest.mark.integration
def test_create_patient_from_referral_requires_core_fields(client, rn_headers):
    resp = client.post(
        "/patients/from-referral",
        json={"first_name": "Missing", "last_name": "Dob"},
        headers=rn_headers,
    )
    assert resp.status_code == 422
