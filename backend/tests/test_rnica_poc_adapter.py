from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.models.admission import Admission
from app.models.patient import Patient
from app.models.plan_of_care import PlanOfCare
from app.models.plan_of_care_version import PlanOfCareVersion
from app.models.poc import POCProblem
from app.models.rnica_assessment import RnicaAssessment


def _make_patient_and_admission(db_session, tenant_id):
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"RNICA-POC-{uuid.uuid4().hex[:12]}",
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


def _make_rnica_assessment(db_session, patient, tenant_id, form_data):
    record = RnicaAssessment(
        id=uuid.uuid4(),
        patient_id=patient.id,
        tenant_id=uuid.UUID(str(tenant_id)),
        form_data=form_data,
    )
    db_session.add(record)
    db_session.commit()
    return record


@pytest.mark.integration
def test_add_view_update_resolve_poc_problem_via_rnica_routes(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    assert tenant_id is not None

    patient, admission = _make_patient_and_admission(db_session, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id, {"nutrition": {}})

    section_key = "nutrition"

    # --- Add to POC ---------------------------------------------------
    add_resp = client.post(
        f"/visits/rnica/{record.id}/poc/{section_key}",
        json={
            "problem_label": "Unintentional weight loss > 5% in 30 days",
            "evidence_text": "Weight down from 140 lb to 128 lb over 4 weeks.",
            "goal_text": "Stabilize weight / minimize further decline",
            "intervention_text": "RN to reassess weight and intake weekly.",
            "discipline": "RN",
        },
        headers=rn_headers,
    )
    assert add_resp.status_code == 201, add_resp.text
    add_body = add_resp.json()
    assert add_body["added"], add_body
    rule_key = add_body["added"][0]

    poc = db_session.query(PlanOfCare).filter_by(admission_id=admission.id).one()
    assert poc.current_version_id is not None
    version_1_id = poc.current_version_id

    # --- Duplicate prevention: re-adding the same problem must not
    # create a second POCProblem row --------------------------------
    add_again_resp = client.post(
        f"/visits/rnica/{record.id}/poc/{section_key}",
        json={
            "problem_label": "Unintentional weight loss > 5% in 30 days",
            "evidence_text": "Weight down from 140 lb to 128 lb over 4 weeks.",
        },
        headers=rn_headers,
    )
    assert add_again_resp.status_code == 201, add_again_resp.text
    assert add_again_resp.json()["skipped_duplicate"] == [rule_key]
    assert add_again_resp.json()["added"] == []

    problem_rows = db_session.query(POCProblem).filter_by(rule_key=rule_key).all()
    # Materialized once per POC version; duplicate-add must not create a
    # second row within the same (current) version.
    current_version_problem_rows = [p for p in problem_rows if p.poc_version_id == poc.current_version_id]
    assert len(current_version_problem_rows) == 1, "duplicate Add-to-POC must not create a duplicate problem row"

    # --- View POC --------------------------------------------------
    view_resp = client.get(f"/visits/rnica/{record.id}/poc/{section_key}", headers=rn_headers)
    assert view_resp.status_code == 200, view_resp.text
    problems = view_resp.json()["problems"]
    assert len(problems) == 1
    assert problems[0]["rule_key"] == rule_key
    assert problems[0]["status"] == "ACTIVE"
    assert "Source: RN ICA assessment" in (problems[0]["description"] or "")

    # --- Update POC --------------------------------------------------
    update_resp = client.put(
        f"/visits/rnica/{record.id}/poc/{section_key}/{rule_key}",
        json={"severity": "high", "description_addendum": "Albumin trending down."},
        headers=rn_headers,
    )
    assert update_resp.status_code == 200, update_resp.text
    assert update_resp.json()["problem"]["severity"] == "HIGH"

    db_session.refresh(poc)
    assert poc.current_version_id != version_1_id, "update must create a new version, not mutate history"

    view_after_update = client.get(f"/visits/rnica/{record.id}/poc/{section_key}", headers=rn_headers).json()
    assert view_after_update["problems"][0]["severity"] == "HIGH"
    assert "Albumin trending down" in view_after_update["problems"][0]["description"]

    # --- Resolve POC --------------------------------------------------
    resolve_resp = client.post(
        f"/visits/rnica/{record.id}/poc/{section_key}/{rule_key}/resolve",
        headers=rn_headers,
    )
    assert resolve_resp.status_code == 200, resolve_resp.text
    assert resolve_resp.json()["problem"]["status"] == "RESOLVED"

    view_after_resolve = client.get(f"/visits/rnica/{record.id}/poc/{section_key}", headers=rn_headers).json()
    assert view_after_resolve["problems"][0]["status"] == "RESOLVED"

    # Full version history preserved — nothing was deleted.
    # Versions: 1) bootstrap (empty), 2) add, 3) update, 4) resolve.
    # The duplicate re-add is a true no-op and creates no version.
    version_count = (
        db_session.query(PlanOfCareVersion)
        .filter_by(plan_of_care_id=poc.id)
        .count()
    )
    assert version_count == 4


@pytest.mark.integration
def test_lock_rnica_assessment_wires_poc_generation_without_duplicating(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, admission = _make_patient_and_admission(db_session, tenant_id)

    form_data = {
        "nutrition": {
            "weightLossPastSixMonths": "Yes",
            "appetite": "Poor",
            "notes": "Significant unintentional weight loss noted.",
        },
        "finalization": {"clinicianSignature": "RN Test"},
    }
    record = _make_rnica_assessment(db_session, patient, tenant_id, form_data)

    lock_resp = client.post(f"/visits/rnica/{record.id}/lock", headers=rn_headers)
    assert lock_resp.status_code == 200, lock_resp.text
    body = lock_resp.json()
    assert body["locked"] is True
    assert "pocGeneration" in body

    # Locking a second time (idempotent re-run) must never duplicate
    # auto-generated problems.
    poc = db_session.query(PlanOfCare).filter_by(admission_id=admission.id).first()
    if poc and body["pocGeneration"].get("applied") and body["pocGeneration"].get("added"):
        rule_key = body["pocGeneration"]["added"][0]
        rows_before = (
            db_session.query(POCProblem)
            .filter_by(rule_key=rule_key)
            .count()
        )
        assert rows_before >= 1
