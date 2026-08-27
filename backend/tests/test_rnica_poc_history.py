from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.models.admission import Admission
from app.models.patient import Patient
from app.models.rnica_assessment import RnicaAssessment
from app.services import rnica_poc_adapter


def _make_patient_and_admission(db_session, tenant_id):
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"RNICA-HIST-{uuid.uuid4().hex[:12]}",
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
def test_history_reflects_creation_update_and_resolve(client, db_session, rn_headers):
    """SECTION 11.B — View History must expose Created By/Date, Last
    Updated By/Date, Status Changes, and Resolve Events, reconstructed
    purely from existing plan_of_care_versions/poc_problems metadata."""
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id, {"skin": {}})
    section_key = "skin"

    add_resp = client.post(
        f"/visits/rnica/{record.id}/poc/{section_key}",
        json={
            "problem_label": "Stage 2 pressure injury, sacrum",
            "evidence_text": "2cm x 1.5cm partial-thickness wound noted on assessment.",
            "goal_text": "Promote wound healing / prevent progression",
            "intervention_text": "RN to assess and dress wound per protocol.",
            "discipline": "RN",
        },
        headers=rn_headers,
    )
    assert add_resp.status_code == 201, add_resp.text
    rule_key = add_resp.json()["added"][0]

    # Immediately after creation: single history entry, no status changes yet.
    hist_resp_1 = client.get(
        f"/visits/rnica/{record.id}/poc/{section_key}/{rule_key}/history",
        headers=rn_headers,
    )
    assert hist_resp_1.status_code == 200, hist_resp_1.text
    hist_1 = hist_resp_1.json()
    assert hist_1["ruleKey"] == rule_key
    assert hist_1["currentStatus"] == "ACTIVE"
    assert hist_1["createdBy"] == "Test User"
    assert hist_1["createdDate"] is not None
    assert hist_1["lastUpdatedBy"] == "Test User"
    assert hist_1["lastUpdatedDate"] == hist_1["createdDate"]
    assert hist_1["statusChanges"] == []
    assert hist_1["resolveEvents"] == []
    assert hist_1["deactivateEvents"] == []

    # Explicit Update (severity change) — should NOT appear as a status
    # change (severity is a distinct field from status).
    update_resp = client.put(
        f"/visits/rnica/{record.id}/poc/{section_key}/{rule_key}",
        json={"severity": "moderate"},
        headers=rn_headers,
    )
    assert update_resp.status_code == 200, update_resp.text

    # Explicit Resolve — must produce exactly one status change + one
    # resolve event.
    resolve_resp = client.post(
        f"/visits/rnica/{record.id}/poc/{section_key}/{rule_key}/resolve",
        headers=rn_headers,
    )
    assert resolve_resp.status_code == 200, resolve_resp.text

    hist_resp_2 = client.get(
        f"/visits/rnica/{record.id}/poc/{section_key}/{rule_key}/history",
        headers=rn_headers,
    )
    assert hist_resp_2.status_code == 200, hist_resp_2.text
    hist_2 = hist_resp_2.json()
    assert hist_2["currentStatus"] == "RESOLVED"
    assert hist_2["createdBy"] == "Test User"
    assert hist_2["createdDate"] == hist_1["createdDate"], "creation record must never change"
    assert hist_2["lastUpdatedBy"] == "Test User"
    assert hist_2["lastUpdatedDate"] != hist_1["createdDate"], "last-updated must advance after resolve"

    assert len(hist_2["statusChanges"]) == 1
    change = hist_2["statusChanges"][0]
    assert change["fromStatus"] == "ACTIVE"
    assert change["toStatus"] == "RESOLVED"
    assert change["changedBy"] == "Test User"
    assert "resolved" in (change["changeReason"] or "").lower()

    assert len(hist_2["resolveEvents"]) == 1
    assert hist_2["deactivateEvents"] == []


@pytest.mark.integration
def test_history_records_deactivate_event(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id, {"nutrition": {}})
    section_key = "nutrition"

    add_resp = client.post(
        f"/visits/rnica/{record.id}/poc/{section_key}",
        json={
            "problem_label": "Poor oral intake",
            "evidence_text": "Family reports <25% meal consumption over past week.",
            "goal_text": "Optimize comfort-focused nutrition",
            "intervention_text": "RN to educate family on comfort feeding.",
            "discipline": "RN",
        },
        headers=rn_headers,
    )
    assert add_resp.status_code == 201, add_resp.text
    rule_key = add_resp.json()["added"][0]

    deactivate_resp = client.post(
        f"/visits/rnica/{record.id}/poc/{section_key}/{rule_key}/deactivate",
        headers=rn_headers,
    )
    assert deactivate_resp.status_code == 200, deactivate_resp.text

    hist_resp = client.get(
        f"/visits/rnica/{record.id}/poc/{section_key}/{rule_key}/history",
        headers=rn_headers,
    )
    assert hist_resp.status_code == 200, hist_resp.text
    hist = hist_resp.json()
    assert hist["currentStatus"] == "HISTORICAL"
    assert len(hist["deactivateEvents"]) == 1
    assert hist["deactivateEvents"][0]["toStatus"] == "HISTORICAL"
    assert hist["resolveEvents"] == []


@pytest.mark.integration
def test_history_404_for_unknown_rule_key(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id, {"skin": {}})

    # No POC/admission bootstrap has happened yet at all for this patient.
    resp = client.get(
        f"/visits/rnica/{record.id}/poc/skin/does-not-exist/history",
        headers=rn_headers,
    )
    assert resp.status_code == 404


def test_get_problem_history_pure_reconstruction_no_http(db_session):
    """Exercises the adapter function directly to confirm the timeline
    reconstruction logic (not just the HTTP wrapper)."""
    tenant_id = uuid.UUID(str(db_session.info.get("tenant_id")))
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)

    with pytest.raises(rnica_poc_adapter.RnicaPocAdapterError):
        rnica_poc_adapter.get_problem_history(
            db_session,
            tenant_id=tenant_id,
            patient_id=patient.id,
            rule_key="nonexistent",
        )
