from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest

from app.core.security import create_access_token
from app.models.admission import Admission
from app.models.clinical_note import ClinicalNote
from app.models.enums import Discipline
from app.models.patient import Patient
from app.models.patient_assignment import PatientAssignment
from app.models.user import User
from app.models.visit import Visit
from tests.conftest import TEST_USER_ID


def _headers(role: str, tenant_id: str) -> dict:
    token = create_access_token(
        user_id=TEST_USER_ID,
        role=role,
        tenant_id=uuid.UUID(str(tenant_id)),
        email=f"{role.lower()}@example.com",
    )
    return {"Authorization": f"Bearer {token}"}


def _make_patient(db_session, tenant_id):
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        mrn=f"VN-{uuid.uuid4().hex[:10]}",
        date_of_birth=date(1942, 5, 5),
        primary_diagnosis="End-stage COPD",
        status="ACTIVE",
        admission_status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _make_admission(db_session, patient, tenant_id):
    admission = Admission(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        patient_id=patient.id,
        admission_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        effective_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        election_signed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        soc_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(admission)
    db_session.commit()
    return admission


def _make_user(db_session, tenant_id, *, role: str, full_name: str) -> User:
    user = User(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        email=f"{full_name.replace(' ', '.').lower()}.{uuid.uuid4().hex[:8]}@example.com",
        full_name=full_name,
        role=role,
        active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _assign(db_session, tenant_id, patient_id, user_id, discipline: Discipline, *, active: bool = True, status: str = "ASSIGNED", is_primary: bool = False):
    assignment = PatientAssignment(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        patient_id=patient_id,
        user_id=user_id,
        discipline=discipline,
        active=active,
        status=status,
        is_primary=is_primary,
        assigned_by=TEST_USER_ID,
    )
    db_session.add(assignment)
    db_session.commit()
    return assignment


def _base_content(visit_date: str, *, pain_level: int = 2):
    return {
        "visit_date": visit_date,
        "time_in": "09:00",
        "form_type": "ASSESS",
        "pain": {"pain_level": pain_level, "controlled": "Y", "other_observation": ""},
        "vitals": {"weight": "140", "mac": "24.5", "bmi": "21.9"},
        "functional_decline": {"pps": 40, "kps": 50, "fast": "6d", "nyha": "III"},
        "signs_symptoms": {
            "nutrition": {"severity": "MODERATE", "oral_intake": "REDUCED", "selected_findings": ["appetite_decline"]},
            "mobility": {"severity": "MODERATE", "ambulatory_status": "LIMITED"},
            "adl_assessment": {"adl_total_score": 12, "adl_scores": {"bathing": 2, "dressing": 2, "toileting": 2, "transferring": 2, "feeding": 2, "grooming": 2}},
            "fall_incidence": {"assessed_no_issues": True},
            "safety_issues": {"assessed_no_issues": True},
        },
        "narrative": "Documented clinical findings.",
    }


def _make_visit_note(
    db_session,
    patient,
    admission,
    *,
    tenant_id,
    visit_date: str,
    finalized: bool,
    pain_level: int = 2,
    content: dict | None = None,
    discipline: str = "RN",
):
    visit_dt = datetime.fromisoformat(f"{visit_date}T09:00:00+00:00")
    visit = Visit(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        patient_id=patient.id,
        admission_id=admission.id,
        provider_id=TEST_USER_ID,
        visit_type=discipline,
        visit_discipline=discipline,
        visit_mode="IN_PERSON",
        status="FINALIZED" if finalized else "DRAFT",
        visit_datetime=visit_dt,
        form_type="ASSESS",
        created_by=TEST_USER_ID,
        updated_by=TEST_USER_ID,
        finalized_by=TEST_USER_ID if finalized else None,
        finalized_at=visit_dt if finalized else None,
    )
    db_session.add(visit)
    db_session.flush()
    note = ClinicalNote(
        id=uuid.uuid4(),
        visit_id=visit.id,
        author_id=TEST_USER_ID,
        tenant_id=uuid.UUID(str(tenant_id)),
        patient_id=patient.id,
        note_type=f"{discipline}_VISIT_NOTE",
        discipline=discipline,
        form_family="CLINICAL",
        form_key=f"{discipline}_VISIT_NOTE",
        module_payload={"form_type": "ASSESS"},
        is_primary_form=True,
        status="FINALIZED" if finalized else "DRAFT",
        encounter_date=visit_dt.date(),
        content=content or _base_content(visit_date, pain_level=pain_level),
        created_by=TEST_USER_ID,
        updated_by_user_id=TEST_USER_ID,
        created_at=visit_dt,
        updated_at=visit_dt,
        finalized_at=visit_dt if finalized else None,
        finalized_by=TEST_USER_ID if finalized else None,
        signed_at=visit_dt if finalized else None,
        signed_by=TEST_USER_ID if finalized else None,
    )
    db_session.add(note)
    db_session.commit()
    return visit, note


@pytest.mark.integration
def test_get_visit_note_returns_comparable_history_and_filters_assignments(client, db_session):
    tenant_id = db_session.info["tenant_id"]
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id)
    other_patient = _make_patient(db_session, tenant_id)
    _assign(db_session, tenant_id, patient.id, TEST_USER_ID, Discipline.RN, is_primary=True)
    hha_active = _make_user(db_session, tenant_id, role="CHHA", full_name="Helpful Aide")
    hha_inactive = _make_user(db_session, tenant_id, role="CHHA", full_name="Inactive Aide")
    lvn_active = _make_user(db_session, tenant_id, role="LVN", full_name="Assigned LVN")
    other_patient_hha = _make_user(db_session, tenant_id, role="CHHA", full_name="Other Patient Aide")
    other_patient_lvn = _make_user(db_session, tenant_id, role="LVN", full_name="Other Patient LVN")
    unrelated_rn = _make_user(db_session, tenant_id, role="RN", full_name="Unrelated RN")
    _assign(db_session, tenant_id, patient.id, hha_active.id, Discipline.CHHA, is_primary=True)
    _assign(db_session, tenant_id, patient.id, hha_inactive.id, Discipline.CHHA, active=False)
    _assign(db_session, tenant_id, patient.id, lvn_active.id, Discipline.LVN)
    _assign(db_session, tenant_id, other_patient.id, other_patient_hha.id, Discipline.CHHA, is_primary=True)
    _assign(db_session, tenant_id, other_patient.id, other_patient_lvn.id, Discipline.LVN)
    _assign(db_session, tenant_id, patient.id, unrelated_rn.id, Discipline.RN)
    _make_visit_note(db_session, patient, admission, tenant_id=tenant_id, visit_date="2026-02-01", finalized=True, pain_level=5)
    _make_visit_note(db_session, patient, admission, tenant_id=tenant_id, visit_date="2026-03-01", finalized=True, pain_level=3)
    current_visit, _ = _make_visit_note(db_session, patient, admission, tenant_id=tenant_id, visit_date="2026-04-01", finalized=False, pain_level=1)

    response = client.get(f"/visits/{current_visit.id}/visit-note", headers=_headers("RN", tenant_id))
    assert response.status_code == 200, response.text
    payload = response.json()
    assert [row["visit_date"] for row in payload["comparable_history"]] == ["2026-03-01", "2026-02-01"]
    assert payload["supervisory_context"]["hha"]["applicable"] is True
    assert payload["supervisory_context"]["lvn_lpn"]["applicable"] is True
    assert [row["name"] for row in payload["supervisory_context"]["hha"]["assignments"]] == ["Helpful Aide"]
    assert [row["name"] for row in payload["supervisory_context"]["lvn_lpn"]["assignments"]] == ["Assigned LVN"]
    assert all(row["name"] != "Other Patient Aide" for row in payload["supervisory_context"]["hha"]["assignments"])
    assert all(row["name"] != "Other Patient LVN" for row in payload["supervisory_context"]["lvn_lpn"]["assignments"])
    assert payload["permissions"]["can_edit_supervisory_review"] is True


@pytest.mark.integration
def test_rn_visit_note_shows_supervisory_section_even_without_active_hha_or_lvn_services(client, db_session):
    tenant_id = db_session.info["tenant_id"]
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id)
    _assign(db_session, tenant_id, patient.id, TEST_USER_ID, Discipline.RN, is_primary=True)
    current_visit, _ = _make_visit_note(db_session, patient, admission, tenant_id=tenant_id, visit_date="2026-04-01", finalized=False)

    response = client.get(f"/visits/{current_visit.id}/visit-note", headers=_headers("RN", tenant_id))
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["supervisory_context"]["visible"] is True
    assert payload["supervisory_context"]["hha"]["applicable"] is False
    assert payload["supervisory_context"]["lvn_lpn"]["applicable"] is False
    assert payload["permissions"]["can_edit_supervisory_review"] is True


@pytest.mark.integration
def test_lvn_visit_note_never_exposes_rn_supervisory_review(client, db_session):
    tenant_id = db_session.info["tenant_id"]
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id)
    _assign(db_session, tenant_id, patient.id, TEST_USER_ID, Discipline.LVN, is_primary=True)
    hha_user = _make_user(db_session, tenant_id, role="CHHA", full_name="Helpful Aide")
    lvn_user = _make_user(db_session, tenant_id, role="LVN", full_name="Assigned LVN")
    _assign(db_session, tenant_id, patient.id, hha_user.id, Discipline.CHHA, is_primary=True)
    _assign(db_session, tenant_id, patient.id, lvn_user.id, Discipline.LVN)
    current_visit, _ = _make_visit_note(
        db_session,
        patient,
        admission,
        tenant_id=tenant_id,
        visit_date="2026-04-01",
        finalized=False,
        discipline="LVN",
    )

    response = client.get(f"/visits/{current_visit.id}/visit-note", headers=_headers("LVN", tenant_id))
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["discipline"] == "LVN"
    assert payload["supervisory_context"]["visible"] is False
    assert payload["supervisory_context"]["hha"]["applicable"] is False
    assert payload["supervisory_context"]["lvn_lpn"]["applicable"] is False
    assert payload["permissions"]["can_edit_supervisory_review"] is False

    content = _base_content("2026-04-01")
    content["supervisory_review"] = {
        "lvn_lpn": {
            "assigned_staff_user_id": str(lvn_user.id),
            "assigned_staff_name": lvn_user.full_name,
            "supervision_type": "PRESENT",
            "observation_datetime": "2026-04-01T09:30",
            "rn_supervisor_name": "Should Not Save",
            "services_meet_patient_needs": "YES",
            "follows_care_plan": "YES",
            "ordered_interventions_completed": "YES",
            "documentation_consistent": "YES",
            "demonstrates_competency": "YES",
            "communication_appropriate": "YES",
            "infection_control_safety": "YES",
            "patient_family_concerns": "NO",
            "corrective_action_required": "NO",
            "notification_documented": "NO",
            "follow_up_required": "NO",
        }
    }
    save_response = client.put(f"/visits/{current_visit.id}/visit-note", json=content, headers=_headers("LVN", tenant_id))
    assert save_response.status_code == 403, save_response.text
    assert "logged-in documenting user role is RN" in save_response.text


@pytest.mark.integration
def test_update_visit_note_round_trips_supervisory_review(client, db_session):
    tenant_id = db_session.info["tenant_id"]
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id)
    _assign(db_session, tenant_id, patient.id, TEST_USER_ID, Discipline.RN, is_primary=True)
    hha_user = _make_user(db_session, tenant_id, role="CHHA", full_name="Helpful Aide")
    lvn_user = _make_user(db_session, tenant_id, role="LVN", full_name="Assigned LVN")
    _assign(db_session, tenant_id, patient.id, hha_user.id, Discipline.CHHA, is_primary=True)
    _assign(db_session, tenant_id, patient.id, lvn_user.id, Discipline.LVN)
    current_visit, _ = _make_visit_note(db_session, patient, admission, tenant_id=tenant_id, visit_date="2026-04-01", finalized=False)

    content = _base_content("2026-04-01")
    content["supervisory_review"] = {
        "hha": {
            "assigned_staff_user_id": str(hha_user.id),
            "assigned_staff_name": hha_user.full_name,
            "supervision_type": "PRESENT",
            "observation_datetime": "2026-04-01T09:30",
            "rn_supervisor_name": "Test User",
            "services_meet_patient_needs": "YES",
            "follows_care_plan": "YES",
            "demonstrates_competency": "YES",
            "communication_appropriate": "YES",
            "infection_control_safety": "YES",
            "patient_family_concerns": "NO",
            "corrective_action_required": "NO",
            "notification_documented": "NO",
            "follow_up_required": "NO",
            "supervisor_comments": "Observed routine care.",
        }
    }

    save_response = client.put(f"/visits/{current_visit.id}/visit-note", json=content, headers=_headers("RN", tenant_id))
    assert save_response.status_code == 200, save_response.text
    saved = save_response.json()
    assert saved["content"]["supervisory_review"]["hha"]["assigned_staff_name"] == "Helpful Aide"
    assert saved["content"]["supervisory_review"]["hha"]["audit"]["updated_by_user_id"] == str(TEST_USER_ID)
    assert saved["content"]["functional_decline"]["pps"] == 40

    reopen_response = client.get(f"/visits/{current_visit.id}/visit-note", headers=_headers("RN", tenant_id))
    assert reopen_response.status_code == 200, reopen_response.text
    reopened = reopen_response.json()
    assert reopened["content"]["supervisory_review"]["hha"]["supervisor_comments"] == "Observed routine care."
    assert reopened["content"]["supervisory_review"]["hha"]["audit"]["created_by_user_id"] == str(TEST_USER_ID)


@pytest.mark.integration
def test_update_visit_note_blocks_supervisory_edit_for_unauthorized_role(client, db_session):
    tenant_id = db_session.info["tenant_id"]
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id)
    _assign(db_session, tenant_id, patient.id, TEST_USER_ID, Discipline.LVN, is_primary=True)
    hha_user = _make_user(db_session, tenant_id, role="CHHA", full_name="Helpful Aide")
    _assign(db_session, tenant_id, patient.id, hha_user.id, Discipline.CHHA, is_primary=True)
    current_visit, _ = _make_visit_note(db_session, patient, admission, tenant_id=tenant_id, visit_date="2026-04-01", finalized=False)

    content = _base_content("2026-04-01")
    content["supervisory_review"] = {
        "hha": {
            "assigned_staff_user_id": str(hha_user.id),
            "assigned_staff_name": hha_user.full_name,
            "supervision_type": "PRESENT",
            "observation_datetime": "2026-04-01T09:30",
            "rn_supervisor_name": "Unauthorized LVN",
            "services_meet_patient_needs": "YES",
            "follows_care_plan": "YES",
            "demonstrates_competency": "YES",
            "communication_appropriate": "YES",
            "infection_control_safety": "YES",
            "patient_family_concerns": "NO",
            "corrective_action_required": "NO",
            "notification_documented": "NO",
            "follow_up_required": "NO",
        }
    }

    response = client.put(f"/visits/{current_visit.id}/visit-note", json=content, headers=_headers("LVN", tenant_id))
    assert response.status_code == 403, response.text
    assert "RN Supervisory Review" in response.text


@pytest.mark.integration
def test_finalize_visit_note_validates_supervisory_requirements_and_finalizes_note(client, db_session):
    tenant_id = db_session.info["tenant_id"]
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id)
    _assign(db_session, tenant_id, patient.id, TEST_USER_ID, Discipline.RN, is_primary=True)
    lvn_user = _make_user(db_session, tenant_id, role="LVN", full_name="Assigned LVN")
    _assign(db_session, tenant_id, patient.id, lvn_user.id, Discipline.LVN)
    current_visit, note = _make_visit_note(db_session, patient, admission, tenant_id=tenant_id, visit_date="2026-04-01", finalized=False)

    invalid_content = _base_content("2026-04-01")
    invalid_content["supervisory_review"] = {
        "lvn_lpn": {
            "assigned_staff_user_id": str(lvn_user.id),
            "assigned_staff_name": lvn_user.full_name,
            "supervision_type": "PRESENT",
            "observation_datetime": "2026-04-01T10:00",
            "rn_supervisor_name": "Test User",
            "services_meet_patient_needs": "NO",
            "follows_care_plan": "YES",
            "ordered_interventions_completed": "YES",
            "documentation_consistent": "YES",
            "demonstrates_competency": "YES",
            "communication_appropriate": "YES",
            "infection_control_safety": "YES",
            "patient_family_concerns": "NO",
            "corrective_action_required": "NO",
            "notification_documented": "NO",
            "follow_up_required": "NO",
        }
    }
    save_invalid = client.put(f"/visits/{current_visit.id}/visit-note", json=invalid_content, headers=_headers("RN", tenant_id))
    assert save_invalid.status_code == 200, save_invalid.text

    finalize_invalid = client.post(f"/visits/{current_visit.id}/finalize", headers=_headers("RN", tenant_id))
    assert finalize_invalid.status_code == 422, finalize_invalid.text
    detail = finalize_invalid.json()["detail"]
    assert detail["code"] == "RN_SUPERVISORY_REVIEW_INVALID"
    assert any("concern details" in message.lower() for message in detail["errors"])

    valid_content = invalid_content.copy()
    valid_content["supervisory_review"] = {
        "lvn_lpn": {
            **invalid_content["supervisory_review"]["lvn_lpn"],
            "concern_details": "Medication setup reviewed and corrected.",
        }
    }
    save_valid = client.put(f"/visits/{current_visit.id}/visit-note", json=valid_content, headers=_headers("RN", tenant_id))
    assert save_valid.status_code == 200, save_valid.text

    finalize_valid = client.post(f"/visits/{current_visit.id}/finalize", headers=_headers("RN", tenant_id))
    assert finalize_valid.status_code == 200, finalize_valid.text
    db_session.refresh(note)
    db_session.refresh(current_visit)
    assert note.status == "FINALIZED"
    assert current_visit.status == "FINALIZED"
    assert note.content["supervisory_review"]["lvn_lpn"]["audit"]["finalized_by_user_id"] == str(TEST_USER_ID)
