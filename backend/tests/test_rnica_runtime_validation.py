from __future__ import annotations

import uuid
from datetime import date, datetime

import pytest

from app.models.admission import Admission
from app.models.patient import Patient
from app.models.rnica_assessment import RnicaAssessment
from app.models.visit import Visit
from tests.conftest import TEST_USER_ID


def _make_linked_visit(db_session, patient, tenant_id):
    """
    A full RNICA lock now finalizes its linked Visit (HOPE-VISIT-HEADER-
    SOT-001), so these runtime-validation tests must exercise the same
    real Visit-creation step the frontend performs before handing RNICA a
    visitId, rather than locking an assessment with no Visit Header link.
    """
    admission = Admission(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient.id,
        status="ACTIVE",
    )
    db_session.add(admission)
    db_session.commit()

    visit = Visit(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        patient_id=patient.id,
        admission_id=admission.id,
        provider_id=TEST_USER_ID,
        visit_type="RN",
        visit_discipline="RN",
        visit_mode="IN_PERSON",
        status="DRAFT",
        visit_datetime=datetime.fromisoformat("2026-01-15T09:00:00+00:00"),
        form_type="INITIAL_ICA",
        created_by=TEST_USER_ID,
        updated_by=TEST_USER_ID,
    )
    db_session.add(visit)
    db_session.commit()
    return visit


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

    visit = _make_linked_visit(db_session, patient, tenant_id)

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
            "visitMeta": {
                "visitDate": "2026-01-15",
                "timeIn": "09:00",
                "timeOut": "10:15",
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
        "visitId": str(visit.id),
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


@pytest.mark.integration
def test_locked_rnica_assessment_status_survives_autosave_put_attempts(client, db_session, rn_headers):
    """
    Checkpoint 1 / Defect A2 regression coverage.

    RNICA_CURRENT_TO_TARGET_GAP_REPORT.md flagged `record.status = "DRAFT"`
    in `update_rnica_assessment` (visits.py) as a possible silent-reset
    defect: a locked/finalized assessment could theoretically be flipped
    back to DRAFT by a trivial autosave PUT.

    Verification of the live code path shows the PUT handler raises
    HTTP 423 (locked) *before* it ever reaches `record.status = "DRAFT"`,
    and no non-DRAFT/non-LOCKED status value is ever assigned to
    RnicaAssessment -- so a locked record's status/locked flag/form_data
    cannot be silently clobbered by an autosave. This test proves that
    invariant against the live HTTP + DB layer, not just by static
    reading, and will fail if that guard is ever removed or reordered.
    """
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

    visit = _make_linked_visit(db_session, patient, tenant_id)

    payload = {
        "patientId": str(patient.id),
        "formData": {
            "demographics": {
                "firstName": "Locked",
                "lastName": "Patient",
                "dob": "1988-07-23",
                "gender": "Female",
                "advancedCarePlanning": {
                    "codeStatus": "Full code",
                    "lifeSustainingTreatmentPreference": "Yes",
                    "hospitalizationPreference": "No",
                },
            },
            "visitMeta": {
                "visitDate": "2026-01-15",
                "timeIn": "09:00",
                "timeOut": "10:15",
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
        "visitId": str(visit.id),
    }

    save_resp = client.post("/visits/rnica/save", json=payload, headers=rn_headers)
    assert save_resp.status_code == 200, save_resp.text
    assessment_id = save_resp.json()["assessmentId"]

    lock_resp = client.post(f"/visits/rnica/{assessment_id}/lock", headers=rn_headers)
    assert lock_resp.status_code == 200, lock_resp.text

    db_session.expire_all()
    locked_record = db_session.query(RnicaAssessment).filter_by(id=uuid.UUID(assessment_id)).one()
    assert locked_record.locked is True
    assert locked_record.status == "LOCKED"

    # Simulate a trivial autosave PUT (e.g. a debounced client-side save
    # firing after the record was locked in another tab/request).
    autosave_payload = {
        "formData": {
            **locked_record.form_data,
            "demographics": {
                **locked_record.form_data["demographics"],
                "firstName": "Tampered",
            },
        }
    }
    put_resp = client.put(
        f"/visits/rnica/{assessment_id}",
        json=autosave_payload,
        headers=rn_headers,
    )
    assert put_resp.status_code == 423, put_resp.text

    db_session.expire_all()
    post_attempt_record = db_session.query(RnicaAssessment).filter_by(id=uuid.UUID(assessment_id)).one()
    assert post_attempt_record.locked is True
    assert post_attempt_record.status == "LOCKED"
    assert post_attempt_record.form_data["demographics"]["firstName"] == "Locked"
