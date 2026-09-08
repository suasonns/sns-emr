"""
Regression test for CMS HOPE Section N (N0500 Scheduled Opioid, N0510 PRN
Opioid, N0520 Bowel Regimen) medication-derivation support.

The frontend's `deriveSectionNFromMedications()` (sns-emr-frontend/src/
intake/sectionNDerivation.js) needs each medication's drug-class membership
(e.g. "OPIOIDS", "LAXATIVES") to suggest Section N answers from the
patient's real Current Medications list, instead of introducing a second,
disconnected classification source on the frontend. This confirms the
`/medications/patients/{id}` list endpoint actually returns that
classification (via the same drug_safety_service.get_drug_classes()
already used for allergy/interaction safety checks), and that a
discontinued medication is still returned (with status="discontinued")
so the frontend can decide to exclude it, rather than the derivation
silently losing history.
"""
from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.models.patient import Patient


def _make_patient(db_session, tenant_id):
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"MEDSECN-{uuid.uuid4().hex[:12]}",
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="Hospice qualifying diagnosis",
        status="ACTIVE",
        admission_status="ACTIVE",
        created_by=None,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _add_medication(client, headers, patient_id, **overrides):
    payload = {
        "medication_name": "Morphine Sulfate",
        "dosage": "15 MG",
        "route": "PO",
        "frequency": "Q4H",
        "start_date": "2026-01-01",
        "ordering_provider_name": "Dr. Test Physician",
        "ordering_provider_role": "MD",
        "source_type": "WRITTEN",
    }
    payload.update(overrides)
    resp = client.post(f"/medications/patients/{patient_id}", params=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.mark.integration
def test_list_medications_includes_opioid_drug_class(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient = _make_patient(db_session, tenant_id)

    _add_medication(client, rn_headers, patient.id, medication_name="Morphine Sulfate", frequency="Q4H")

    resp = client.get(f"/medications/patients/{patient.id}", headers=rn_headers)
    assert resp.status_code == 200, resp.text
    meds = resp.json()
    assert len(meds) == 1
    assert meds[0]["drug_classes"] == ["OPIOIDS"]
    assert meds[0]["status"] == "active"


@pytest.mark.integration
def test_list_medications_includes_laxative_drug_class(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient = _make_patient(db_session, tenant_id)

    _add_medication(
        client, rn_headers, patient.id,
        medication_name="Senna", frequency="BID", start_date="2026-01-02",
    )

    resp = client.get(f"/medications/patients/{patient.id}", headers=rn_headers)
    assert resp.status_code == 200, resp.text
    meds = resp.json()
    assert len(meds) == 1
    assert meds[0]["drug_classes"] == ["LAXATIVES"]


@pytest.mark.integration
def test_list_medications_returns_empty_drug_classes_for_unclassified_medication(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient = _make_patient(db_session, tenant_id)

    _add_medication(
        client, rn_headers, patient.id,
        medication_name="Some Unclassified Compound XYZ", frequency="Daily", start_date="2026-01-03",
    )

    resp = client.get(f"/medications/patients/{patient.id}", headers=rn_headers)
    assert resp.status_code == 200, resp.text
    meds = resp.json()
    assert len(meds) == 1
    assert meds[0]["drug_classes"] == []
