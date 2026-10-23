from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from app.models.admission import Admission
from app.models.patient import Patient
from app.models.patient_allergy import PatientAllergy
from app.models.patient_facesheet import PatientFaceSheet
from app.models.rnica_assessment import RnicaAssessment
from tests.conftest import TEST_USER_ID

# PRODUCT OWNER DIRECTIVE (2026-10-13) "Investigate allergy inconsistency" --
# regression coverage for the patient-safety bug where the Face Sheet's
# allergy banner (`patient_facesheets.has_allergies`/`allergies`, read by
# RNICACommandWorkspace.jsx's `formatAllergies`) disagreed with Infection's
# AllergiesCard (which reads the live `patient_allergies` table). Root
# cause: `_sync_facesheet_from_rnica` (app/api/visits.py) rebuilt the
# banner from `form_data.infection.allergies`, a field RNICA.jsx's
# AllergiesCard never writes to -- it was always `[]`, so every RNICA save
# forcibly overwrote the banner to "No Known Allergies" regardless of what
# was actually documented in the structured Allergies module. Fixed to
# read the same `patient_allergies` table Infection already treats as
# authoritative.


def _make_patient_with_facesheet(db_session, tenant_id):
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"ALLERGY-SYNC-{uuid.uuid4().hex[:10]}",
        date_of_birth=date(1945, 3, 3),
        primary_diagnosis="Hospice qualifying diagnosis",
        status="ACTIVE",
        admission_status="ADMITTED",
        created_by=None,
    )
    db_session.add(patient)
    db_session.flush()

    facesheet = PatientFaceSheet(
        tenant_id=tenant_id,
        patient_id=patient.id,
        first_name="Test",
        last_name="Patient",
        dob=date(1945, 3, 3),
        has_allergies=False,
        allergies=None,
        created_by=TEST_USER_ID,
        updated_by=TEST_USER_ID,
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(facesheet)

    admission = Admission(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient.id,
        status="ACTIVE",
    )
    db_session.add(admission)
    db_session.commit()
    return patient, facesheet, admission


def _make_rnica_assessment(db_session, patient, tenant_id, admission, form_data):
    record = RnicaAssessment(
        id=uuid.uuid4(),
        patient_id=patient.id,
        tenant_id=uuid.UUID(str(tenant_id)),
        admission_id=admission.id,
        form_data=form_data,
    )
    db_session.add(record)
    db_session.commit()
    return record


def test_rnica_save_does_not_blank_facesheet_allergies_when_structured_allergies_exist(
    client, db_session, rn_headers
):
    """Reproduces the reported bug: a nurse documents a structured allergy
    via the Infection AllergiesCard (POST /patients/{id}/allergies, the
    real `patient_allergies` table) while the RNICA form_data's dead
    `infection.allergies` field stays `[]`. Saving/updating the RNICA
    assessment must not overwrite the Face Sheet banner back to NKA."""
    tenant_id = db_session.info.get("tenant_id")
    patient, facesheet, admission = _make_patient_with_facesheet(db_session, tenant_id)

    # Document a real, structured allergy the way Infection's AllergiesCard
    # does -- never touching RNICA form_data.
    db_session.add(
        PatientAllergy(
            patient_id=patient.id,
            allergen_text="Penicillin",
            allergen_type="DRUG",
            severity="SEVERE",
            active=True,
        )
    )
    db_session.commit()

    record = _make_rnica_assessment(
        db_session,
        patient,
        tenant_id,
        admission,
        {"infection": {"allergies": []}},
    )

    update_resp = client.put(
        f"/visits/rnica/{record.id}",
        json={"formData": {"infection": {"allergies": []}}},
        headers=rn_headers,
    )
    assert update_resp.status_code == 200, update_resp.text

    db_session.refresh(facesheet)
    assert facesheet.has_allergies is True
    assert facesheet.allergies is not None
    assert "Penicillin" in facesheet.allergies


def test_rnica_save_marks_facesheet_nka_when_no_active_structured_allergies(
    client, db_session, rn_headers
):
    tenant_id = db_session.info.get("tenant_id")
    patient, facesheet, admission = _make_patient_with_facesheet(db_session, tenant_id)
    facesheet.has_allergies = True
    facesheet.allergies = "stale text from a prior visit"
    db_session.commit()

    record = _make_rnica_assessment(
        db_session, patient, tenant_id, admission, {"infection": {"allergies": []}}
    )

    update_resp = client.put(
        f"/visits/rnica/{record.id}",
        json={"formData": {"infection": {"allergies": []}}},
        headers=rn_headers,
    )
    assert update_resp.status_code == 200, update_resp.text

    db_session.refresh(facesheet)
    assert facesheet.has_allergies is False
    assert facesheet.allergies is None


def test_rnica_save_ignores_inactive_removed_allergies(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, facesheet, admission = _make_patient_with_facesheet(db_session, tenant_id)

    db_session.add(
        PatientAllergy(
            patient_id=patient.id,
            allergen_text="Shellfish",
            allergen_type="FOOD",
            active=False,
        )
    )
    db_session.commit()

    record = _make_rnica_assessment(
        db_session, patient, tenant_id, admission, {"infection": {"allergies": []}}
    )

    update_resp = client.put(
        f"/visits/rnica/{record.id}",
        json={"formData": {"infection": {"allergies": []}}},
        headers=rn_headers,
    )
    assert update_resp.status_code == 200, update_resp.text

    db_session.refresh(facesheet)
    assert facesheet.has_allergies is False
    assert facesheet.allergies is None
