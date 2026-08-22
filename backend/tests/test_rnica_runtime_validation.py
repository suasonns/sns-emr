from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.models.patient import Patient
from app.models.rnica_assessment import RnicaAssessment


@pytest.mark.integration
def test_rnica_assessment_save_get_update_and_lock(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    assert tenant_id is not None

    patient = db_session.query(Patient).filter_by(tenant_id=tenant_id).first()
    if patient is None:
        patient = Patient(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            mrn=f"RNICA-{uuid.uuid4().hex[:12]}",
            date_of_birth=date(1988, 7, 23),
            primary_diagnosis="Hospice qualifying diagnosis",
            status="ACTIVE",
            admission_status="PRE_REFERRAL",
            created_by=None,
        )
        db_session.add(patient)
        db_session.commit()

    payload = {
        "patientId": str(patient.id),
        "formData": {
            "demographics": {
                "firstName": "Jane",
                "lastName": "Doe",
                "dob": "1988-07-23",
                "gender": "Female",
                "advancedCarePlanning": {
                    "codeStatus": "Full code",
                    "lifeSustainingTreatmentPreference": "Yes",
                    "hospitalizationPreference": "No",
                },
            },
            "finalization": {
                "clinicianSignature": "RN Test",
                "signatureCertification": True,
                "pocGenerationCompleted": True,
                "responseToInterventions": {"baselineEstablished": True},
            },
            "diagnoses": {"lcdEligibilityNarrative": "Documented decline per LCD criteria."},
            "referrals": {"reviewed": True},
        },
    }

    save_resp = client.post("/visits/rnica/save", json=payload, headers=rn_headers)
    assert save_resp.status_code == 200, save_resp.text
    assessment_id = save_resp.json()["assessmentId"]

    get_resp = client.get(f"/visits/rnica/{assessment_id}", headers=rn_headers)
    assert get_resp.status_code == 200, get_resp.text
    assert get_resp.json()["formData"]["demographics"]["firstName"] == "Jane"

    update_payload = {
        "formData": {
            **get_resp.json()["formData"],
            "demographics": {
                **get_resp.json()["formData"]["demographics"],
                "firstName": "Janet",
            },
        }
    }
    update_resp = client.put(
        f"/visits/rnica/{assessment_id}",
        json=update_payload,
        headers=rn_headers,
    )
    assert update_resp.status_code == 200, update_resp.text
    assert update_resp.json()["status"] == "updated"

    lock_resp = client.post(f"/visits/rnica/{assessment_id}/lock", headers=rn_headers)
    assert lock_resp.status_code == 200, lock_resp.text
    assert lock_resp.json()["status"] == "locked"

    db_record = db_session.query(RnicaAssessment).filter_by(id=uuid.UUID(assessment_id)).one()
    assert db_record.locked is True
    assert db_record.status == "LOCKED"
