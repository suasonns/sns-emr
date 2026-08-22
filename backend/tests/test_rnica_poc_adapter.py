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
def test_lock_rnica_assessment_creates_no_poc_version_or_problem(client, db_session, rn_headers):
    """Locking RN ICA must only validate/sign/lock/preserve data — it must
    never create a PlanOfCareVersion or POCProblem. POC changes are strictly
    clinician-initiated via the explicit Add/Update/Resolve routes."""
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
    assert body["status"] == "locked"
    # The lock response must not carry any POC-generation payload.
    assert "pocGeneration" not in body

    db_session.refresh(record)
    assert record.locked is True
    assert record.status == "LOCKED"

    # No PlanOfCare, PlanOfCareVersion, or POCProblem was created as a
    # side effect of locking.
    assert db_session.query(PlanOfCare).filter_by(admission_id=admission.id).first() is None
    assert db_session.query(PlanOfCareVersion).count() == 0
    assert db_session.query(POCProblem).count() == 0

    # Locking a second time is likewise a no-op for POC.
    lock_resp_2 = client.post(f"/visits/rnica/{record.id}/lock", headers=rn_headers)
    assert lock_resp_2.status_code == 200, lock_resp_2.text
    assert db_session.query(PlanOfCare).filter_by(admission_id=admission.id).first() is None
    assert db_session.query(POCProblem).count() == 0


@pytest.mark.integration
def test_update_and_resolve_require_explicit_action(client, db_session, rn_headers):
    """A problem added to the POC must remain untouched (no severity
    change, no status change) until an explicit Update/Resolve call is
    made — proving neither happens implicitly as a side effect of any
    other RN ICA action (e.g. saving/locking the assessment)."""
    tenant_id = db_session.info.get("tenant_id")
    patient, admission = _make_patient_and_admission(db_session, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id, {"skin": {}})
    section_key = "skin"

    add_resp = client.post(
        f"/visits/rnica/{record.id}/poc/{section_key}",
        json={
            "problem_label": "Stage 2 pressure injury, sacrum",
            "evidence_text": "2cm x 1.5cm partial-thickness wound noted on assessment.",
        },
        headers=rn_headers,
    )
    assert add_resp.status_code == 201, add_resp.text
    rule_key = add_resp.json()["added"][0]

    problem = db_session.query(POCProblem).filter_by(rule_key=rule_key).one()
    assert problem.status == "ACTIVE"
    assert problem.severity == "UNKNOWN"
    version_after_add = problem.poc_version_id

    # Locking the assessment (an unrelated action) must not update or
    # resolve the POC problem.
    lock_resp = client.post(f"/visits/rnica/{record.id}/lock", headers=rn_headers)
    assert lock_resp.status_code == 200, lock_resp.text

    unchanged = db_session.query(POCProblem).filter_by(rule_key=rule_key).one()
    assert unchanged.status == "ACTIVE"
    assert unchanged.severity == "UNKNOWN"
    assert unchanged.poc_version_id == version_after_add

    # Only the explicit Update route changes severity.
    update_resp = client.put(
        f"/visits/rnica/{record.id}/poc/{section_key}/{rule_key}",
        json={"severity": "moderate"},
        headers=rn_headers,
    )
    assert update_resp.status_code == 200, update_resp.text
    assert update_resp.json()["problem"]["severity"] == "MODERATE"

    still_active = db_session.query(POCProblem).filter_by(rule_key=rule_key).order_by(POCProblem.created_at.desc()).first()
    assert still_active.status == "ACTIVE", "explicit Update must not resolve the problem"

    # Only the explicit Resolve route changes status.
    resolve_resp = client.post(
        f"/visits/rnica/{record.id}/poc/{section_key}/{rule_key}/resolve",
        headers=rn_headers,
    )
    assert resolve_resp.status_code == 200, resolve_resp.text
    assert resolve_resp.json()["problem"]["status"] == "RESOLVED"


@pytest.mark.integration
def test_skin_wound_structured_fields_save_reload_and_preserve_existing_data(client, db_session, rn_headers):
    """Master Map §5.11 structured wound fields persist through the
    existing RNICA form_data JSONB model, round-trip on reload, and never
    disturb pre-existing skin fields (Braden, skinStatus, skinBodySites,
    woundImpairment, notes)."""
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)

    initial_form_data = {
        "skin": {
            "skinConditionsPresent": True,
            "skinStatus": ["Dry", "Fragile"],
            "skinTurgor": "Fair",
            "skinBodySites": ["sacrum", "left-heel"],
            "braden": {
                "sensoryPerception": "2", "moisture": "2", "activity": "2",
                "mobility": "2", "nutrition": "3", "frictionShear": "2", "total": "13",
            },
            "pressureInjuryRisk": "High (≤14)",
            "woundImpairment": "Pre-existing free-text wound note.",
            "notes": "Pre-existing skin notes.",
        },
    }
    record = _make_rnica_assessment(db_session, patient, tenant_id, initial_form_data)

    # Add structured wound data + plan-level fields, as the frontend
    # WoundListCard / "Wound Documentation & Notes" card would.
    wound_entry = {
        "presentAsPressureInjury": True,
        "stage": "Stage 2",
        "woundType": "Pressure injury",
        "location": "Sacrum",
        "length": 2.0,
        "width": 1.5,
        "depth": 0.3,
        "drainage": "Small",
        "odor": "None",
        "periwoundCondition": "Intact, mild erythema",
        "isSkinTear": False,
        "isSurgicalWound": False,
        "isNonhealingWound": False,
        "currentTreatment": "Hydrocolloid dressing",
        "dressing": "Hydrocolloid",
        "dressingFrequency": "Every 3 days",
    }
    updated_skin = {
        **initial_form_data["skin"],
        "wounds": [wound_entry],
        "pressureReliefMeasures": ["Pressure-relief mattress", "Frequent position changes"],
        "repositioningPlan": "Reposition every 2 hours, alternate sides",
    }
    update_resp = client.put(
        f"/visits/rnica/{record.id}",
        json={"formData": {"skin": updated_skin}},
        headers=rn_headers,
    )
    assert update_resp.status_code == 200, update_resp.text

    # Reload and confirm both the new structured fields AND the
    # pre-existing skin fields all round-trip intact.
    get_resp = client.get(f"/visits/rnica/{record.id}", headers=rn_headers)
    assert get_resp.status_code == 200, get_resp.text
    skin = get_resp.json()["formData"]["skin"]

    # New §5.11 structured fields.
    assert len(skin["wounds"]) == 1
    reloaded_wound = skin["wounds"][0]
    for key, value in wound_entry.items():
        assert reloaded_wound[key] == value, f"wound field {key} did not round-trip"
    assert skin["pressureReliefMeasures"] == ["Pressure-relief mattress", "Frequent position changes"]
    assert skin["repositioningPlan"] == "Reposition every 2 hours, alternate sides"

    # Pre-existing skin fields untouched.
    assert skin["skinConditionsPresent"] is True
    assert skin["skinStatus"] == ["Dry", "Fragile"]
    assert skin["skinTurgor"] == "Fair"
    assert skin["skinBodySites"] == ["sacrum", "left-heel"]
    assert skin["braden"]["total"] == "13"
    assert skin["pressureInjuryRisk"] == "High (≤14)"
    assert skin["woundImpairment"] == "Pre-existing free-text wound note."
    assert skin["notes"] == "Pre-existing skin notes."

    # POC linkage from the skin section still works end-to-end after the
    # structured wound fields are present.
    add_resp = client.post(
        f"/visits/rnica/{record.id}/poc/skin",
        json={
            "problem_label": "Stage 2 pressure injury, sacrum",
            "evidence_text": "2.0cm x 1.5cm x 0.3cm wound, small serous drainage, no odor.",
        },
        headers=rn_headers,
    )
    assert add_resp.status_code == 201, add_resp.text
    assert add_resp.json()["added"], add_resp.json()

    view_resp = client.get(f"/visits/rnica/{record.id}/poc/skin", headers=rn_headers)
    assert view_resp.status_code == 200, view_resp.text
    assert len(view_resp.json()["problems"]) == 1