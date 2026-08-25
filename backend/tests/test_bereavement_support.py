from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.core.security import create_access_token
from app.models.bereavement_communication_note import BereavementCommunicationNote
from app.models.patient import Patient
from app.models.tenant import Tenant
from app.models.user import User
from tests.conftest import TEST_USER_ID


def _headers(user_id: uuid.UUID, role: str, tenant_id: uuid.UUID) -> dict[str, str]:
    token = create_access_token(
        user_id=user_id,
        role=role,
        tenant_id=tenant_id,
        email=f"{role.lower()}@example.com",
    )
    return {"Authorization": f"Bearer {token}"}


def _make_patient(db_session, tenant_id: uuid.UUID, *, mrn_prefix: str = "BSUP") -> Patient:
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"{mrn_prefix}-{uuid.uuid4().hex[:10]}",
        date_of_birth=date(1940, 3, 3),
        primary_diagnosis="Hospice bereavement support test diagnosis",
        status="ACTIVE",
        admission_status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _ensure_tenant_and_user(db_session, tenant_id: uuid.UUID, user_id: uuid.UUID, *, role: str = "MSW") -> None:
    if db_session.get(Tenant, tenant_id) is None:
        db_session.add(
            Tenant(
                id=tenant_id,
                legal_name=f"Tenant {tenant_id.hex[:8]}",
                display_name=f"Tenant {tenant_id.hex[:8]}",
                npi=f"{int(str(tenant_id.int)[:10]):010d}",
                tenant_type="DEV",
                status="ACTIVE",
            )
        )
        db_session.commit()
    if db_session.get(User, user_id) is None:
        db_session.add(
            User(
                id=user_id,
                tenant_id=tenant_id,
                email=f"user.{user_id.hex[:8]}@example.com",
                full_name="Bereavement Support Test User",
                role=role,
                active=True,
            )
        )
        db_session.commit()


@pytest.mark.integration
class TestBereavementSupportApi:
    def test_summary_falls_back_to_poc_when_no_post_death_assessment(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id)

        poc_resp = client.post(
            "/bereavement-poc",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={
                "patient_id": str(patient.id),
                "date_of_death": "2026-03-01",
                "risk_level": "MODERATE",
                "primary_first_name": "Jane",
                "primary_last_name": "Doe",
                "primary_relationship_to_patient": "Spouse",
            },
        )
        assert poc_resp.status_code == 201, poc_resp.text
        poc_id = poc_resp.json()["id"]

        response = client.get(
            f"/bereavement-support/patient/{patient.id}/summary",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["source_bereavement_poc_id"] == poc_id
        assert body["source_post_death_assessment_id"] is None
        assert body["risk_level"] == "MODERATE"
        assert body["primary_bereaved"]["primary_first_name"] == "Jane"
        assert body["primary_bereaved"]["primary_last_name"] == "Doe"
        assert body["death_facts"] is None  # POC has no death-facts fields

    def test_summary_prefers_post_death_assessment_for_death_facts(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="BSUP2")

        poc_resp = client.post(
            "/bereavement-poc",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={
                "patient_id": str(patient.id),
                "date_of_death": "2026-03-01",
                "risk_level": "MODERATE",
                "primary_first_name": "Jane",
                "primary_last_name": "Doe",
            },
        )
        poc_id = poc_resp.json()["id"]

        pd_resp = client.post(
            "/post-death-bereavement",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={
                "patient_id": str(patient.id),
                "bereavement_poc_id": poc_id,
                "date_of_death": "2026-03-01",
                "place_of_death": "HOME",
                "death_expected": True,
                "funeral_home_name": "Rest Haven Funeral Home",
            },
        )
        assert pd_resp.status_code == 201, pd_resp.text
        pd_id = pd_resp.json()["id"]

        response = client.get(
            f"/bereavement-support/patient/{patient.id}/summary",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["source_post_death_assessment_id"] == pd_id
        assert body["death_facts"]["place_of_death"] == "HOME"
        assert body["death_facts"]["funeral_home_name"] == "Rest Haven Funeral Home"
        # Primary bereaved inherited from the linked POC onto the assessment.
        assert body["primary_bereaved"]["primary_first_name"] == "Jane"

    def test_summary_empty_when_no_records(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="BSUP3")

        response = client.get(
            f"/bereavement-support/patient/{patient.id}/summary",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["primary_bereaved"] is None
        assert body["death_facts"] is None
        assert body["risk_level"] is None
        assert body["goals"] == []

    def test_calendar_reflects_letter_tracker_touchpoints(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="BSUP4")

        tracker_resp = client.post(
            "/bereavement-letters",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(patient.id), "date_of_death": "2026-01-01", "risk_level": "HIGH"},
        )
        assert tracker_resp.status_code == 201, tracker_resp.text

        response = client.get(
            f"/bereavement-support/patient/{patient.id}/calendar",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
        )
        assert response.status_code == 200, response.text
        body = response.json()
        # HIGH risk = 13 total touchpoints, all carrying due dates.
        assert len(body["events"]) == 13
        assert all(e["risk_level"] == "HIGH" for e in body["events"])
        assert body["events"] == sorted(body["events"], key=lambda e: e["due_date"])

    def test_calendar_excludes_discontinued_trackers(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="BSUP5")

        tracker_resp = client.post(
            "/bereavement-letters",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(patient.id), "date_of_death": "2026-01-01", "risk_level": "LOW"},
        )
        tracker_id = tracker_resp.json()["id"]

        discontinue_resp = client.patch(
            f"/bereavement-letters/{tracker_id}",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"status": "DISCONTINUED", "discontinued_reason": "Family requested no further contact"},
        )
        assert discontinue_resp.status_code == 200, discontinue_resp.text

        response = client.get(
            f"/bereavement-support/patient/{patient.id}/calendar",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
        )
        assert response.status_code == 200, response.text
        assert response.json()["events"] == []

    def test_create_and_list_communication_notes(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="BSUP6")

        create_resp = client.post(
            f"/bereavement-support/patient/{patient.id}/notes",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={
                "contact_date": "2026-03-10",
                "contact_type": "PHONE",
                "contact_with": "Primary bereaved -- Jane Doe",
                "summary": "Called to check in; family coping well, no additional needs identified.",
            },
        )
        assert create_resp.status_code == 201, create_resp.text
        note_body = create_resp.json()
        assert note_body["contact_type"] == "PHONE"
        assert note_body["created_by"] == str(TEST_USER_ID)

        stored = db_session.get(BereavementCommunicationNote, uuid.UUID(note_body["id"]))
        assert stored is not None
        assert stored.summary.startswith("Called to check in")

        # A second note, older by contact_date, to verify descending order.
        client.post(
            f"/bereavement-support/patient/{patient.id}/notes",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={
                "contact_date": "2026-02-01",
                "contact_type": "VISIT",
                "summary": "Home visit; delivered sympathy card in person.",
            },
        )

        list_resp = client.get(
            f"/bereavement-support/patient/{patient.id}/notes",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
        )
        assert list_resp.status_code == 200, list_resp.text
        notes = list_resp.json()
        assert len(notes) == 2
        assert notes[0]["contact_date"] == "2026-03-10"  # most recent first
        assert notes[1]["contact_date"] == "2026-02-01"

    def test_rejects_invalid_contact_type(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="BSUP7")

        response = client.post(
            f"/bereavement-support/patient/{patient.id}/notes",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"contact_date": "2026-03-10", "contact_type": "CARRIER_PIGEON", "summary": "n/a"},
        )
        assert response.status_code == 400

    def test_rejects_tracker_link_from_other_patient(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="BSUP8")
        other_patient = _make_patient(db_session, tenant_id, mrn_prefix="BSUP9")

        tracker_resp = client.post(
            "/bereavement-letters",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(other_patient.id), "date_of_death": "2026-01-01", "risk_level": "LOW"},
        )
        tracker_id = tracker_resp.json()["id"]

        response = client.post(
            f"/bereavement-support/patient/{patient.id}/notes",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={
                "contact_date": "2026-03-10",
                "contact_type": "EMAIL",
                "summary": "n/a",
                "bereavement_letter_tracker_id": tracker_id,
            },
        )
        assert response.status_code == 404
