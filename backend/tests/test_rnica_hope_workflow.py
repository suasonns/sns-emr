from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from app.models.admission import Admission
from app.models.msw_ica_assessment import MswIcaAssessment
from app.models.patient import Patient
from app.models.rnica_assessment import RnicaAssessment
from app.models.scica_assessment import ScicaAssessment
from app.services.eligibility.engine import detect_lcd_config
from tests.conftest import TEST_USER_ID


def _make_patient(db_session, tenant_id):
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"HOPE-{uuid.uuid4().hex[:12]}",
        date_of_birth=date(1941, 7, 4),
        primary_diagnosis="Chronic systolic (congestive) heart failure",
        status="ACTIVE",
        admission_status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _make_admission(db_session, patient, tenant_id, election_date: datetime):
    admission = Admission(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient.id,
        admission_date=election_date,
        effective_date=election_date,
        election_signed_at=election_date,
        soc_date=election_date,
        status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(admission)
    db_session.commit()
    return admission


def _complete_form_data(**overrides):
    base = {
        "visitMeta": {"discipline": "RN"},
        "diagnoses": {
            "primaryDiagnosis": {
                "icd10": "I50.22",
                "description": "Chronic systolic (congestive) heart failure",
            },
            "lcdEligibilityNarrative": "Documented terminal decline supports hospice eligibility.",
        },
        "vitals": {"height": "70", "weight": "140"},
        "pain": {"painIntensity": {"current": 5}},
        "musculoskeletal": {
            "adlBathing": "Independent",
            "adlDressing": "Needs assistance",
            "adlToileting": "Dependent",
            "adlTransfers": "Independent",
            "adlAmbulation": "Needs assistance",
            "adlFeeding": "Independent",
        },
        "performanceStatus": {"pps": "50", "kps": "60", "nyha": "Class III", "fast": "6d"},
        "referrals": {"reviewed": True},
        "finalization": {
            "clinicianSignature": "RN Test",
            "signatureCertification": True,
            "pocGenerationCompleted": True,
            "responseToInterventions": {"baselineEstablished": True},
            "hopeSubmissionNumber": "",
            "hopeAlreadySubmitted": False,
        },
    }
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merged = dict(base[key])
            merged.update(value)
            base[key] = merged
        else:
            base[key] = value
    return base


def _make_assessment(
    db_session,
    patient,
    admission,
    tenant_id,
    *,
    assessment_type="RNICA",
    locked=False,
    locked_at: datetime | None = None,
    form_data=None,
):
    record = RnicaAssessment(
        id=uuid.uuid4(),
        patient_id=patient.id,
        tenant_id=uuid.UUID(str(tenant_id)),
        admission_id=admission.id,
        assessment_type=assessment_type,
        status="LOCKED" if locked else "DRAFT",
        locked=locked,
        locked_at=locked_at,
        form_data=form_data or _complete_form_data(),
    )
    db_session.add(record)
    db_session.commit()
    return record


def _make_msw_assessment(db_session, patient, *, locked_at: datetime):
    record = MswIcaAssessment(
        id=uuid.uuid4(),
        patient_id=patient.id,
        assessment_type="MSWICA",
        status="LOCKED",
        locked=True,
        locked_at=locked_at,
        form_data={},
    )
    db_session.add(record)
    db_session.commit()
    return record


def _make_sc_assessment(db_session, patient, *, locked_at: datetime):
    record = ScicaAssessment(
        id=uuid.uuid4(),
        patient_id=patient.id,
        assessment_type="SCICA",
        status="LOCKED",
        locked=True,
        locked_at=locked_at,
        form_data={},
    )
    db_session.add(record)
    db_session.commit()
    return record


@pytest.mark.integration
def test_save_update_assessment_persists_type_and_lists_by_patient(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient = _make_patient(db_session, tenant_id)
    _make_admission(db_session, patient, tenant_id, datetime(2026, 1, 1, tzinfo=timezone.utc))

    save_resp = client.post(
        "/visits/rnica/save",
        json={
            "patientId": str(patient.id),
            "assessmentSubtype": "update",
            "formData": _complete_form_data(),
        },
        headers=rn_headers,
    )
    assert save_resp.status_code == 200, save_resp.text
    saved = save_resp.json()
    assert saved["assessmentType"] == "UPDATE"

    record_resp = client.get(f"/visits/rnica/{saved['assessmentId']}", headers=rn_headers)
    assert record_resp.status_code == 200, record_resp.text
    record = record_resp.json()
    assert record["assessmentType"] == "UPDATE"
    assert record["hopeWorkflow"]["status"] == "OPEN"
    assert record["formData"]["diagnoses"]["ndsEligibility"]["detectedDisease"] == "HEART_FAILURE"

    list_resp = client.get(
        f"/visits/rnica/by-patient/{patient.id}/records",
        params={"assessmentType": "UPDATE"},
        headers=rn_headers,
    )
    assert list_resp.status_code == 200, list_resp.text
    listed = list_resp.json()["assessments"]
    assert len(listed) == 1
    assert listed[0]["assessmentType"] == "UPDATE"


@pytest.mark.integration
def test_locked_assessment_keeps_clinical_immutability_but_allows_hope_workflow_updates(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id, datetime(2026, 1, 1, tzinfo=timezone.utc))
    record = _make_assessment(
        db_session,
        patient,
        admission,
        tenant_id,
        locked=True,
        locked_at=datetime(2026, 1, 2, 9, 0, tzinfo=timezone.utc),
    )

    edit_resp = client.put(
        f"/visits/rnica/{record.id}",
        json={"formData": _complete_form_data(vitals={"height": "70", "weight": "150"})},
        headers=rn_headers,
    )
    assert edit_resp.status_code == 423, edit_resp.text

    close_resp = client.post(f"/visits/rnica/{record.id}/hope-workflow/close", headers=rn_headers)
    assert close_resp.status_code == 200, close_resp.text
    assert close_resp.json()["hopeWorkflow"]["status"] == "CLOSED"

    ready_resp = client.post(f"/visits/rnica/{record.id}/hope-workflow/ready", headers=rn_headers)
    assert ready_resp.status_code == 200, ready_resp.text
    assert ready_resp.json()["hopeWorkflow"]["status"] == "READY_TO_EXPORT"

    export_resp = client.post(
        f"/visits/rnica/{record.id}/hope-workflow/export",
        json={"batch_id": "BATCH-42"},
        headers=rn_headers,
    )
    assert export_resp.status_code == 200, export_resp.text
    assert export_resp.json()["hopeWorkflow"]["status"] == "EXPORTED_TO_BATCH"
    assert export_resp.json()["hopeWorkflow"]["exportBatchId"] == "BATCH-42"

    submit_resp = client.patch(
        f"/visits/rnica/{record.id}/hope-submission",
        json={"hopeSubmissionNumber": "HOPE-SUB-1001", "hopeAlreadySubmitted": True},
        headers=rn_headers,
    )
    assert submit_resp.status_code == 200, submit_resp.text
    assert submit_resp.json()["hopeWorkflow"]["status"] == "SUBMITTED"
    assert submit_resp.json()["hopeWorkflow"]["submissionNumber"] == "HOPE-SUB-1001"

    unlock_blocked = client.post(
        f"/visits/rnica/{record.id}/hope-workflow/unlock",
        json={"reason": "Need to reopen export workflow."},
        headers=rn_headers,
    )
    assert unlock_blocked.status_code == 409, unlock_blocked.text

    clear_submit_resp = client.patch(
        f"/visits/rnica/{record.id}/hope-submission",
        json={"hopeSubmissionNumber": "", "hopeAlreadySubmitted": False},
        headers=rn_headers,
    )
    assert clear_submit_resp.status_code == 200, clear_submit_resp.text
    assert clear_submit_resp.json()["hopeWorkflow"]["status"] == "EXPORTED_TO_BATCH"

    inactivate_resp = client.patch(
        f"/visits/rnica/{record.id}/hope-inactivation",
        json={"inactivated": True},
        headers=rn_headers,
    )
    assert inactivate_resp.status_code == 200, inactivate_resp.text
    assert inactivate_resp.json()["hopeWorkflow"]["status"] == "INACTIVATED"

    reactivate_resp = client.patch(
        f"/visits/rnica/{record.id}/hope-inactivation",
        json={"inactivated": False},
        headers=rn_headers,
    )
    assert reactivate_resp.status_code == 200, reactivate_resp.text
    assert reactivate_resp.json()["hopeWorkflow"]["status"] == "EXPORTED_TO_BATCH"

    unlock_resp = client.post(
        f"/visits/rnica/{record.id}/hope-workflow/unlock",
        json={"reason": "Batch needs correction before resubmission."},
        headers=rn_headers,
    )
    assert unlock_resp.status_code == 200, unlock_resp.text
    assert unlock_resp.json()["hopeWorkflow"]["status"] == "OPEN"

    workflow_resp = client.get(f"/visits/rnica/{record.id}/hope-workflow", headers=rn_headers)
    assert workflow_resp.status_code == 200, workflow_resp.text
    assert workflow_resp.json()["hopeWorkflow"]["unlockReason"] == "Batch needs correction before resubmission."


@pytest.mark.integration
def test_hope_update_status_finds_huv1_and_huv2_windows(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    election_date = datetime(2026, 2, 1, 8, 0, tzinfo=timezone.utc)
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id, election_date)

    huv1 = _make_assessment(
        db_session,
        patient,
        admission,
        tenant_id,
        assessment_type="UPDATE",
        locked=True,
        locked_at=election_date + timedelta(days=7),
        form_data=_complete_form_data(visitMeta={"discipline": "RN", "visitDate": "2026-02-08"}),
    )
    huv2 = _make_assessment(
        db_session,
        patient,
        admission,
        tenant_id,
        assessment_type="UPDATE",
        locked=True,
        locked_at=election_date + timedelta(days=18),
        form_data=_complete_form_data(visitMeta={"discipline": "RN", "visitDate": "2026-02-19"}),
    )

    resp = client.get(f"/visits/rnica/hope-update-status/{patient.id}", headers=rn_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["huv1"]["assessment"]["assessmentId"] == str(huv1.id)
    assert body["huv2"]["assessment"]["assessmentId"] == str(huv2.id)
    assert body["huv1"]["window"]["start"] == "2026-02-07"
    assert body["huv2"]["window"]["end"] == "2026-03-03"


@pytest.mark.integration
def test_decline_of_status_trend_returns_locked_admission_and_update_points(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id, datetime(2026, 3, 1, tzinfo=timezone.utc))

    _make_assessment(
        db_session,
        patient,
        admission,
        tenant_id,
        assessment_type="RNICA",
        locked=True,
        locked_at=datetime(2026, 3, 2, 9, 0, tzinfo=timezone.utc),
        form_data=_complete_form_data(
            pain={"painIntensity": {"current": 6}},
            performanceStatus={"pps": "50", "kps": "60", "nyha": "Class III", "fast": "6d"},
        ),
    )
    _make_assessment(
        db_session,
        patient,
        admission,
        tenant_id,
        assessment_type="UPDATE",
        locked=True,
        locked_at=datetime(2026, 3, 15, 9, 0, tzinfo=timezone.utc),
        form_data=_complete_form_data(
            pain={"painIntensity": {"current": 4}},
            performanceStatus={"pps": "40", "kps": "50", "nyha": "Class IV", "fast": "7a"},
            vitals={"height": "70", "weight": "132"},
        ),
    )

    resp = client.get(f"/patients/{patient.id}/decline-of-status-trend", headers=rn_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    trend = body["trend"]
    assert [point["assessment_type"] for point in trend] == ["ADMISSION", "UPDATE"]
    assert trend[0]["kps"] == 60.0
    assert trend[1]["pain_level"] == 4.0
    assert trend[1]["mac"] is None
    assert trend[1]["nyha_label"] == "Class IV"
    assert body["available_from_date"] == "2026-03-02"
    assert body["available_to_date"] == "2026-03-15"

    filtered = client.get(
        f"/patients/{patient.id}/decline-of-status-trend",
        params={"from_date": "2026-03-10", "to_date": "2026-03-20"},
        headers=rn_headers,
    )
    assert filtered.status_code == 200, filtered.text
    filtered_trend = filtered.json()["trend"]
    assert len(filtered_trend) == 1
    assert filtered_trend[0]["assessment_type"] == "UPDATE"


@pytest.mark.integration
def test_assessment_history_returns_reusable_combined_records_with_filters(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    election_date = datetime(2026, 4, 1, 8, 0, tzinfo=timezone.utc)
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id, election_date)

    rn_admission = _make_assessment(
        db_session,
        patient,
        admission,
        tenant_id,
        assessment_type="RNICA",
        locked=True,
        locked_at=election_date + timedelta(days=1),
        form_data=_complete_form_data(visitMeta={"discipline": "RN", "visitDate": "2026-04-02"}),
    )
    rn_update = _make_assessment(
        db_session,
        patient,
        admission,
        tenant_id,
        assessment_type="UPDATE",
        locked=True,
        locked_at=election_date + timedelta(days=7),
        form_data=_complete_form_data(visitMeta={"discipline": "RN", "visitDate": "2026-04-08"}),
    )
    msw = _make_msw_assessment(db_session, patient, locked_at=election_date + timedelta(days=2))
    sc = _make_sc_assessment(db_session, patient, locked_at=election_date + timedelta(days=3))

    resp = client.get(
        f"/patients/{patient.id}/assessment-history",
        params={"sort_order": "asc", "limit": 50, "offset": 0},
        headers=rn_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["patient_id"] == str(patient.id)
    assert body["total"] == 4
    assert [item["discipline"] for item in body["items"]] == ["RN", "MSW", "SC", "RN"]
    assert body["items"][0]["record_id"] == str(rn_admission.id)
    assert body["items"][0]["record_url_hint"]["section"] == "nursing-assessment"
    assert body["items"][3]["record_id"] == str(rn_update.id)
    assert body["items"][3]["phase_hint"] == "HUV1"
    assert any(item["record_id"] == str(msw.id) and item["discipline"] == "MSW" for item in body["items"])
    assert any(item["record_id"] == str(sc.id) and item["discipline"] == "SC" for item in body["items"])

    filtered = client.get(
        f"/patients/{patient.id}/assessment-history",
        params={"discipline": "RN", "assessment_type": "UPDATE", "from_date": "2026-04-05"},
        headers=rn_headers,
    )
    assert filtered.status_code == 200, filtered.text
    filtered_items = filtered.json()["items"]
    assert len(filtered_items) == 1
    assert filtered_items[0]["record_id"] == str(rn_update.id)
    assert filtered_items[0]["assessment_type"] == "UPDATE"


def test_detect_lcd_config_prefers_heart_failure_for_chf_icd10():
    detected = detect_lcd_config(
        {
            "primary_diagnosis_code": "I50.22",
            "primary_diagnosis_description": "Chronic systolic (congestive) heart failure",
        }
    )
    assert detected["disease"] == "HEART_FAILURE"
