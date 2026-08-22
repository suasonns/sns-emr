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


@pytest.mark.integration
def test_infection_structured_fields_save_reload_and_poc_linkage(client, db_session, rn_headers):
    """Master Map §5.4 Immunological/Infection structured fields (allergies,
    antibiotic-resistant infection, history of resistant infection, current
    active infection, antibiotic use, temperature, recurrent infection,
    infection history) persist through the existing RNICA form_data JSONB
    model, round-trip on reload, and coexist with POC controls on the
    infection section."""
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)

    record = _make_rnica_assessment(db_session, patient, tenant_id, {"infection": {}})

    updated_infection = {
        "allergies": ["Food allergies", "Sensitivities"],
        "allergyDetails": "Shellfish; adhesive tape sensitivity.",
        "immunosuppressed": True,
        "precautions": ["Contact"],
        "antibioticResistantInfection": ["MRSA"],
        "historyOfResistantInfections": ["C. difficile"],
        "currentInfections": ["UTI", "Wound"],
        "antibioticUse": True,
        "temperature": "100.4",
        "recurrentInfection": True,
        "infectionHistory": "Recurrent UTIs over past year, 3 courses of antibiotics.",
        "notes": "Wound culture pending.",
    }
    update_resp = client.put(
        f"/visits/rnica/{record.id}",
        json={"formData": {"infection": updated_infection}},
        headers=rn_headers,
    )
    assert update_resp.status_code == 200, update_resp.text

    get_resp = client.get(f"/visits/rnica/{record.id}", headers=rn_headers)
    assert get_resp.status_code == 200, get_resp.text
    infection = get_resp.json()["formData"]["infection"]

    for key, value in updated_infection.items():
        assert infection[key] == value, f"infection field {key} did not round-trip"

    # POC linkage from the infection section works end-to-end.
    add_resp = client.post(
        f"/visits/rnica/{record.id}/poc/infection",
        json={
            "problem_label": "Active infection risk — recurrent UTI, MRSA history",
            "evidence_text": "Temp 100.4F, MRSA on current culture, recurrent UTI history.",
        },
        headers=rn_headers,
    )
    assert add_resp.status_code == 201, add_resp.text
    assert add_resp.json()["added"], add_resp.json()

    view_resp = client.get(f"/visits/rnica/{record.id}/poc/infection", headers=rn_headers)
    assert view_resp.status_code == 200, view_resp.text
    assert len(view_resp.json()["problems"]) == 1


@pytest.mark.integration
def test_endocrine_structured_fields_save_reload_and_poc_linkage(client, db_session, rn_headers):
    """Master Map §5.7 Endocrine structured fields (impairment domain,
    diabetes dependency classification, oral hypoglycemics, current
    treatment) persist through the existing RNICA form_data JSONB model,
    round-trip on reload, and coexist with POC controls on the endocrine
    section."""
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)

    record = _make_rnica_assessment(db_session, patient, tenant_id, {"endocrine": {}})

    updated_endocrine = {
        "endocrineImpairment": ["Thyroid", "Pancreas"],
        "thyroid": {"assessment": "Enlarged", "notes": "Palpable nodule, referred to endocrinology."},
        "diabetes": {
            "type": "Type 2",
            "dependency": "Insulin-dependent",
            "glucoseMonitoring": "BID",
            "lastHbA1c": "8.2",
            "lastHbA1cDate": "2026-07-01",
            "insulinType": "Lantus",
            "insulinDose": "20 units qHS",
            "oralHypoglycemics": ["Metformin"],
        },
        "endocrineSymptoms": ["Fatigue", "Polyuria"],
        "symptomSeverity": {"Fatigue": "Moderate"},
        "currentEndocrineMeds": ["Insulin", "Levothyroxine"],
        "notes": "Blood glucose trending high this week.",
    }
    update_resp = client.put(
        f"/visits/rnica/{record.id}",
        json={"formData": {"endocrine": updated_endocrine}},
        headers=rn_headers,
    )
    assert update_resp.status_code == 200, update_resp.text

    get_resp = client.get(f"/visits/rnica/{record.id}", headers=rn_headers)
    assert get_resp.status_code == 200, get_resp.text
    endocrine = get_resp.json()["formData"]["endocrine"]

    for key, value in updated_endocrine.items():
        assert endocrine[key] == value, f"endocrine field {key} did not round-trip"

    # POC linkage from the endocrine section works end-to-end.
    add_resp = client.post(
        f"/visits/rnica/{record.id}/poc/endocrine",
        json={
            "problem_label": "Glucose-management problem — insulin-dependent, HbA1c 8.2",
            "evidence_text": "Poorly controlled Type 2 diabetes, HbA1c 8.2, fatigue and polyuria present.",
        },
        headers=rn_headers,
    )
    assert add_resp.status_code == 201, add_resp.text
    assert add_resp.json()["added"], add_resp.json()

    view_resp = client.get(f"/visits/rnica/{record.id}/poc/endocrine", headers=rn_headers)
    assert view_resp.status_code == 200, view_resp.text
    assert len(view_resp.json()["problems"]) == 1


@pytest.mark.integration
def test_cardiovascular_structured_fields_save_reload_and_poc_linkage(client, db_session, rn_headers):
    """Master Map §5.2 Cardiovascular structured fields (pulse sites,
    expanded pulse characteristics, pacemaker/defibrillator, varicose
    veins, central venous line, cool extremities, stasis ulcer, skin
    color) persist through the existing RNICA form_data JSONB model,
    round-trip on reload, and coexist with POC controls on the
    cardiovascular section."""
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)

    record = _make_rnica_assessment(db_session, patient, tenant_id, {"cardiovascular": {}})

    updated_cardio = {
        "bpSymptoms": ["Hypertensive"],
        "pulseSites": ["Apical", "Pedal"],
        "pulseQuality": "Tachycardia",
        "edema": {"present": "Yes", "location": ["Bilateral lower extremities"], "severity": "2+", "pitting": ""},
        "chestPain": {"present": "No", "type": "", "frequency": ""},
        "peripheralCirculation": "Diminished",
        "heartSounds": "S1S2 regular, no murmur",
        "jvd": "No",
        "skinColor": "Pale",
        "pacemaker": True,
        "internalDefibrillator": False,
        "varicoseVeins": True,
        "centralVenousLine": False,
        "coolExtremities": True,
        "stasisUlcer": False,
        "notes": "Bilateral pedal pulses weak but palpable.",
    }
    update_resp = client.put(
        f"/visits/rnica/{record.id}",
        json={"formData": {"cardiovascular": updated_cardio}},
        headers=rn_headers,
    )
    assert update_resp.status_code == 200, update_resp.text

    get_resp = client.get(f"/visits/rnica/{record.id}", headers=rn_headers)
    assert get_resp.status_code == 200, get_resp.text
    cardio = get_resp.json()["formData"]["cardiovascular"]

    for key, value in updated_cardio.items():
        assert cardio[key] == value, f"cardiovascular field {key} did not round-trip"

    # POC linkage from the cardiovascular section works end-to-end.
    add_resp = client.post(
        f"/visits/rnica/{record.id}/poc/cardiovascular",
        json={
            "problem_label": "Perfusion concern — pacemaker, cool extremities, weak pedal pulses",
            "evidence_text": "Cool extremities, weak pedal/apical pulses, tachycardia noted, pacemaker present.",
        },
        headers=rn_headers,
    )
    assert add_resp.status_code == 201, add_resp.text
    assert add_resp.json()["added"], add_resp.json()

    view_resp = client.get(f"/visits/rnica/{record.id}/poc/cardiovascular", headers=rn_headers)
    assert view_resp.status_code == 200, view_resp.text
    assert len(view_resp.json()["problems"]) == 1


@pytest.mark.integration
def test_respiratory_structured_fields_save_reload_and_poc_linkage(client, db_session, rn_headers):
    """Master Map §5.3 Respiratory structured fields (treatment declined,
    expanded exertion level / lung sounds / respirations / cough options,
    oxygen delivery mode / room air, and ventilator/airway support)
    persist through the existing RNICA form_data JSONB model, round-trip
    on reload, and coexist with POC controls on the respiratory
    section."""
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)

    record = _make_rnica_assessment(db_session, patient, tenant_id, {"respiratory": {}})

    updated_respiratory = {
        "sobSeverity": "Moderate",
        "treatmentDeclined": False,
        "exertionLevel": "Pursed-lip breathing",
        "shortnessOfBreathScreened": True,
        "screeningDate": "2026-08-01",
        "treatmentInitiated": True,
        "treatmentDate": "2026-08-02",
        "lungSounds": ["Crackles", "Rales"],
        "respirations": ["Tachypnea", "Orthopnea"],
        "coughType": "Barrel chest",
        "sputumCharacter": "Thick yellow",
        "oxygenTherapy": {
            "inUse": True, "type": "Nasal cannula", "litersPerMinute": "2",
            "hoursPerDay": "24", "satOnO2": "92",
            "deliveryMode": "Continuous", "onRoomAir": False,
        },
        "ventilator": {
            "shortTermVentilator": False, "longTermVentilator": True,
            "ventilatorTypeAndSettings": "AC 14/450/40% FiO2",
            "tracheostomyType": "Cuffed", "tracheostomySize": "6.0",
        },
        "notes": "Patient on long-term vent via tracheostomy.",
    }
    update_resp = client.put(
        f"/visits/rnica/{record.id}",
        json={"formData": {"respiratory": updated_respiratory}},
        headers=rn_headers,
    )
    assert update_resp.status_code == 200, update_resp.text

    get_resp = client.get(f"/visits/rnica/{record.id}", headers=rn_headers)
    assert get_resp.status_code == 200, get_resp.text
    respiratory = get_resp.json()["formData"]["respiratory"]

    for key, value in updated_respiratory.items():
        assert respiratory[key] == value, f"respiratory field {key} did not round-trip"

    # POC linkage from the respiratory section works end-to-end.
    add_resp = client.post(
        f"/visits/rnica/{record.id}/poc/respiratory",
        json={
            "problem_label": "Long-term ventilator dependence via tracheostomy",
            "evidence_text": "AC 14/450/40% FiO2, cuffed trach size 6.0, SpO2 92% on 2L NC.",
        },
        headers=rn_headers,
    )
    assert add_resp.status_code == 201, add_resp.text
    assert add_resp.json()["added"], add_resp.json()

    view_resp = client.get(f"/visits/rnica/{record.id}/poc/respiratory", headers=rn_headers)
    assert view_resp.status_code == 200, view_resp.text
    assert len(view_resp.json()["problems"]) == 1


@pytest.mark.integration
def test_gastrointestinal_structured_fields_save_reload_and_poc_linkage(client, db_session, rn_headers):
    """Master Map §5.5 Gastrointestinal structured fields (vomiting
    occurrences in 24 hours, expanded abdomen findings, ascites,
    abdominal girth, stool characteristics, expanded bowel status,
    bowel frequency, and reason bowel regimen could not be initiated)
    persist through the existing RNICA form_data JSONB model,
    round-trip on reload, and coexist with POC controls on the
    gastrointestinal section."""
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)

    record = _make_rnica_assessment(db_session, patient, tenant_id, {"gastrointestinal": {}})

    updated_gi = {
        "nausea": "Mild",
        "vomiting": "Moderate",
        "vomitingOccurrences24h": "3",
        "diarrhea": "None",
        "constipation": "None",
        "bowelSounds": "Hypoactive",
        "abdomen": "Tympanic",
        "ascites": True,
        "abdominalGirth": "38 in",
        "stoolCharacter": ["Bloody"],
        "bowelStatus": "Impaction",
        "bowelFrequency": "Every 3-4 days",
        "reasonBowelRegimenNotInitiated": "Patient declined per family request pending IDG discussion.",
        "lastBM": "2026-08-18",
        "continence": "Incontinent",
        "feedingTube": {"present": False, "type": "", "site": ""},
        "ostomy": {"present": False, "type": "", "condition": ""},
        "notes": "Abdomen distended, tympanic to percussion, ascites suspected.",
    }
    update_resp = client.put(
        f"/visits/rnica/{record.id}",
        json={"formData": {"gastrointestinal": updated_gi}},
        headers=rn_headers,
    )
    assert update_resp.status_code == 200, update_resp.text

    get_resp = client.get(f"/visits/rnica/{record.id}", headers=rn_headers)
    assert get_resp.status_code == 200, get_resp.text
    gi = get_resp.json()["formData"]["gastrointestinal"]

    for key, value in updated_gi.items():
        assert gi[key] == value, f"gastrointestinal field {key} did not round-trip"

    # POC linkage from the gastrointestinal section works end-to-end.
    add_resp = client.post(
        f"/visits/rnica/{record.id}/poc/gastrointestinal",
        json={
            "problem_label": "Bowel impaction with bloody stool, ascites",
            "evidence_text": "Impaction, bloody stool, ascites, abdominal girth 38in, last BM 8/18.",
        },
        headers=rn_headers,
    )
    assert add_resp.status_code == 201, add_resp.text
    assert add_resp.json()["added"], add_resp.json()

    view_resp = client.get(f"/visits/rnica/{record.id}/poc/gastrointestinal", headers=rn_headers)
    assert view_resp.status_code == 200, view_resp.text
    assert len(view_resp.json()["problems"]) == 1


@pytest.mark.integration
def test_genitourinary_structured_fields_save_reload_and_poc_linkage(client, db_session, rn_headers):
    """Master Map §5.8 Genitourinary/Reproductive structured fields
    (expanded continence options, general urine characteristics/color,
    expanded catheter type, catheter irrigation, and catheter care)
    persist through the existing RNICA form_data JSONB model,
    round-trip on reload, and coexist with POC controls on the
    genitourinary section."""
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)

    record = _make_rnica_assessment(db_session, patient, tenant_id, {"genitourinary": {}})

    updated_gu = {
        "urinaryStatus": "Retention",
        "frequency": "Every 2 hours",
        "urineCharacteristics": ["Cloudy", "Odor"],
        "urineColor": "Dark amber",
        "catheter": {
            "present": True, "type": "Urostomy", "size": "16 Fr",
            "insertionDate": "2026-07-01", "lastChangeDate": "2026-08-01",
            "condition": "Patent", "urineCharacteristics": ["Cloudy", "Foul odor"],
            "irrigation": {"solution": "Normal saline", "frequency": "Daily", "duration": "15 min"},
        },
        "catheterCare": "Stoma site cleaned, appliance changed, no skin breakdown noted.",
        "urineOutput": "Decreased",
        "twentyFourHourVolume": "450",
        "reproductive": {"concerns": [], "notes": ""},
        "bladderManagement": ["Scheduled toileting"],
        "notes": "Urostomy functioning well, output decreased today.",
    }
    update_resp = client.put(
        f"/visits/rnica/{record.id}",
        json={"formData": {"genitourinary": updated_gu}},
        headers=rn_headers,
    )
    assert update_resp.status_code == 200, update_resp.text

    get_resp = client.get(f"/visits/rnica/{record.id}", headers=rn_headers)
    assert get_resp.status_code == 200, get_resp.text
    gu = get_resp.json()["formData"]["genitourinary"]

    for key, value in updated_gu.items():
        assert gu[key] == value, f"genitourinary field {key} did not round-trip"

    # POC linkage from the genitourinary section works end-to-end.
    add_resp = client.post(
        f"/visits/rnica/{record.id}/poc/genitourinary",
        json={
            "problem_label": "Urinary-elimination problem — retention, decreased output via urostomy",
            "evidence_text": "Retention noted, urostomy output decreased to 450mL/24h, cloudy urine with odor.",
        },
        headers=rn_headers,
    )
    assert add_resp.status_code == 201, add_resp.text
    assert add_resp.json()["added"], add_resp.json()

    view_resp = client.get(f"/visits/rnica/{record.id}/poc/genitourinary", headers=rn_headers)
    assert view_resp.status_code == 200, view_resp.text
    assert len(view_resp.json()["problems"]) == 1


@pytest.mark.integration
def test_sleep_rest_structured_fields_save_reload_and_poc_linkage(client, db_session, rn_headers):
    """Master Map §5.9 Sleep/Rest structured fields (exact spec sleep
    pattern options, nighttime symptoms, and response to interventions)
    persist through the existing RNICA form_data JSONB model, round-trip
    on reload, and coexist with POC controls on the neurological section
    (Sleep/Rest is a subcard within Neurological)."""
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)

    record = _make_rnica_assessment(db_session, patient, tenant_id, {"neurological": {}})

    updated_sleep_rest = {
        "sleepPattern": "Lack of sleep",
        "averageSleepHours": "3",
        "sleepAids": ["Medication"],
        "nighttimeSymptoms": ["Pain", "Restlessness"],
        "response": "Partial relief after PRN morphine dose.",
        "restfulness": "Inadequate",
        "notes": "Patient reports frequent awakening due to pain.",
    }
    update_resp = client.put(
        f"/visits/rnica/{record.id}",
        json={"formData": {"neurological": {"sleepRest": updated_sleep_rest}}},
        headers=rn_headers,
    )
    assert update_resp.status_code == 200, update_resp.text

    get_resp = client.get(f"/visits/rnica/{record.id}", headers=rn_headers)
    assert get_resp.status_code == 200, get_resp.text
    sleep_rest = get_resp.json()["formData"]["neurological"]["sleepRest"]

    for key, value in updated_sleep_rest.items():
        assert sleep_rest[key] == value, f"sleepRest field {key} did not round-trip"

    # POC linkage from the neurological section (which hosts Sleep/Rest)
    # works end-to-end.
    add_resp = client.post(
        f"/visits/rnica/{record.id}/poc/neurological",
        json={
            "problem_label": "Sleep-pattern disturbance — pain-related lack of sleep",
            "evidence_text": "Averaging 3 hours sleep/night, pain and restlessness reported, partial relief with PRN morphine.",
        },
        headers=rn_headers,
    )
    assert add_resp.status_code == 201, add_resp.text
    assert add_resp.json()["added"], add_resp.json()

    view_resp = client.get(f"/visits/rnica/{record.id}/poc/neurological", headers=rn_headers)
    assert view_resp.status_code == 200, view_resp.text
    assert len(view_resp.json()["problems"]) == 1


def test_musculoskeletal_structured_fields_save_reload_and_poc_linkage(client, db_session, rn_headers):
    """Master Map §5.10 Musculoskeletal structured fields (Issues checklist,
    ROM-loss location, Disability classification, and Additional items —
    Strength/Balance/Pain with movement) persist through the existing
    RNICA form_data JSONB model, round-trip on reload, and coexist with
    POC controls on the musculoskeletal section."""
    tenant_id = db_session.info.get("tenant_id")
    patient, _admission = _make_patient_and_admission(db_session, tenant_id)

    record = _make_rnica_assessment(db_session, patient, tenant_id, {"musculoskeletal": {}})

    updated_musculoskeletal = {
        "weakness": "Moderate",
        "rigidity": "Mild",
        "contractures": "None",
        "paralysis": "Right hemiparesis",
        "contracturesLocation": [],
        "romLimitations": ["Upper extremities", "Neck/spine"],
        "musculoskeletalIssues": ["Joint swelling", "Spasms / cramps", "Prosthesis"],
        "strength": "Decreased",
        "balance": "Impaired",
        "painWithMovement": "Moderate",
        "gait": "Unsteady",
        "assistiveDevices": ["Walker"],
        "fallHistory": {"fallsLast90Days": "1", "fallInjuries": "None"},
        "mobility": {"ambulatoryStatus": "Assisted", "endurance": "Fair", "transferAbility": "Standby assist"},
        "adl": {"bathing": "3", "dressing": "2", "toileting": "2", "transferring": "3", "eating": "0", "grooming": "1"},
        "notes": "Right-sided weakness following recent CVA; fall precautions in place.",
    }
    update_resp = client.put(
        f"/visits/rnica/{record.id}",
        json={"formData": {"musculoskeletal": updated_musculoskeletal}},
        headers=rn_headers,
    )
    assert update_resp.status_code == 200, update_resp.text

    get_resp = client.get(f"/visits/rnica/{record.id}", headers=rn_headers)
    assert get_resp.status_code == 200, get_resp.text
    musculoskeletal = get_resp.json()["formData"]["musculoskeletal"]

    for key, value in updated_musculoskeletal.items():
        assert musculoskeletal[key] == value, f"musculoskeletal field {key} did not round-trip"

    # POC linkage from the musculoskeletal section works end-to-end.
    add_resp = client.post(
        f"/visits/rnica/{record.id}/poc/musculoskeletal",
        json={
            "problem_label": "Fall risk — right hemiparesis with impaired balance",
            "evidence_text": "Right hemiparesis, decreased strength, impaired balance, 1 fall in last 90 days.",
        },
        headers=rn_headers,
    )
    assert add_resp.status_code == 201, add_resp.text
    assert add_resp.json()["added"], add_resp.json()

    view_resp = client.get(f"/visits/rnica/{record.id}/poc/musculoskeletal", headers=rn_headers)
    assert view_resp.status_code == 200, view_resp.text
    assert len(view_resp.json()["problems"]) == 1