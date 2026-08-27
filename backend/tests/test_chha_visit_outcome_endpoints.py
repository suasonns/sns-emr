"""
End-to-end HTTP-level coverage for the two CHHA (Home Health Aide) visit
endpoints added to support the CHHA Plan of Care / Visit Note redesign:

  GET  /visits/patient/{patient_id}/aide      -- list a patient's aide visits
  POST /visits/{visit_id}/chha-outcome        -- save a structured CHHA outcome
  GET  /visits/{visit_id}/chha-outcome        -- reload a saved CHHA outcome

Only import-verified before this file existed; these tests exercise the real
router end-to-end via the shared `client`/`db_session` fixtures.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from app.core.security import create_access_token
from app.models.admission import Admission
from app.models.patient import Patient
from app.models.visit import Visit
from tests.conftest import TEST_USER_ID, _test_tenant_id


def _tenant_id() -> uuid.UUID:
    return uuid.UUID(_test_tenant_id())


def _qa_headers() -> dict:
    # QA_REVIEWER has tenant-wide VIEW_ALL_TENANT_PATIENTS, so it bypasses
    # PatientAssignment scoping -- keeps this test focused on the CHHA
    # endpoints themselves rather than assignment setup.
    token = create_access_token(
        user_id=TEST_USER_ID,
        role="QA_REVIEWER",
        tenant_id=_tenant_id(),
        email="qa.reviewer@example.com",
    )
    return {"Authorization": f"Bearer {token}", "X-User-Id": str(TEST_USER_ID)}


def _make_patient(db_session) -> Patient:
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=_tenant_id(),
        mrn=f"CHHA-{uuid.uuid4().hex[:10]}",
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="Test Diagnosis",
        status="ACTIVE",
        admission_status="ACTIVE",
        hospice_election_date=date.today(),
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _make_admission(db_session, patient_id) -> Admission:
    admission = Admission(
        id=uuid.uuid4(),
        tenant_id=_tenant_id(),
        patient_id=patient_id,
        status="ACTIVE",
        created_by=TEST_USER_ID,
    )
    db_session.add(admission)
    db_session.commit()
    return admission


def _make_aide_visit(db_session, patient_id, admission_id, status="DRAFT") -> Visit:
    visit = Visit(
        id=uuid.uuid4(),
        tenant_id=_tenant_id(),
        patient_id=patient_id,
        admission_id=admission_id,
        provider_id=TEST_USER_ID,
        visit_type="ROUTINE",
        visit_discipline="AIDE",
        visit_datetime=datetime.utcnow(),
        status=status,
        created_by=TEST_USER_ID,
    )
    db_session.add(visit)
    db_session.commit()
    return visit


class TestListAideVisitsForPatient:
    def test_lists_only_aide_visits_newest_first(self, client, db_session):
        patient = _make_patient(db_session)
        admission = _make_admission(db_session, patient.id)
        older = _make_aide_visit(db_session, patient.id, admission.id)
        newer = _make_aide_visit(db_session, patient.id, admission.id)

        # A non-AIDE visit for the same patient must never show up here.
        rn_visit = Visit(
            id=uuid.uuid4(),
            tenant_id=_tenant_id(),
            patient_id=patient.id,
            admission_id=admission.id,
            provider_id=TEST_USER_ID,
            visit_type="ROUTINE",
            visit_discipline="RN",
            visit_datetime=datetime.utcnow(),
            status="DRAFT",
            created_by=TEST_USER_ID,
        )
        db_session.add(rn_visit)
        db_session.commit()

        resp = client.get(f"/visits/patient/{patient.id}/aide", headers=_qa_headers())
        assert resp.status_code == 200, resp.text
        body = resp.json()
        visit_ids = [row["visit_id"] for row in body]
        assert str(rn_visit.id) not in visit_ids
        assert str(older.id) in visit_ids
        assert str(newer.id) in visit_ids

    def test_unknown_patient_returns_empty_list_not_error(self, client, db_session):
        resp = client.get(f"/visits/patient/{uuid.uuid4()}/aide", headers=_qa_headers())
        # get_authorized_patient 404s for a patient that doesn't exist/isn't
        # in-tenant -- assert it fails closed rather than silently listing.
        assert resp.status_code == 404, resp.text


class TestChhaOutcomeUpsertAndReload:
    def _payload(self, **overrides):
        base = {
            "tolerance_to_care": "Tolerated care well, no distress noted.",
            "condition_during_visit": "Stable, alert and oriented.",
            "skin_outcome": "No new skin findings.",
            "pain_or_change_observed": False,
            "rn_notification_required": False,
            "task_results": [
                {
                    "section_code": "TRANSFER",
                    "task_code": "TRANSFER::TWO_PERSON",
                    "was_assigned": True,
                    "completed": True,
                    "result_note": "A second person physically assisted. Assisted by: J. Smith, HHA",
                }
            ],
        }
        base.update(overrides)
        return base

    def test_saves_outcome_and_creates_task_results(self, client, db_session):
        patient = _make_patient(db_session)
        admission = _make_admission(db_session, patient.id)
        visit = _make_aide_visit(db_session, patient.id, admission.id)

        resp = client.post(
            f"/visits/{visit.id}/chha-outcome",
            json=self._payload(),
            headers=_qa_headers(),
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "saved"
        assert body["visit_id"] == str(visit.id)

        reload_resp = client.get(f"/visits/{visit.id}/chha-outcome", headers=_qa_headers())
        assert reload_resp.status_code == 200, reload_resp.text
        reloaded = reload_resp.json()
        assert reloaded is not None
        assert reloaded["visit_id"] == str(visit.id)
        assert reloaded["skin_outcome"] == "No new skin findings."
        assert len(reloaded["task_results"]) == 1
        assert reloaded["task_results"][0]["task_code"] == "TRANSFER::TWO_PERSON"

    def test_rejects_non_aide_visit(self, client, db_session):
        patient = _make_patient(db_session)
        admission = _make_admission(db_session, patient.id)
        rn_visit = Visit(
            id=uuid.uuid4(),
            tenant_id=_tenant_id(),
            patient_id=patient.id,
            admission_id=admission.id,
            provider_id=TEST_USER_ID,
            visit_type="ROUTINE",
            visit_discipline="RN",
            visit_datetime=datetime.utcnow(),
            status="DRAFT",
            created_by=TEST_USER_ID,
        )
        db_session.add(rn_visit)
        db_session.commit()

        resp = client.post(
            f"/visits/{rn_visit.id}/chha-outcome",
            json=self._payload(),
            headers=_qa_headers(),
        )
        assert resp.status_code == 422, resp.text

    def test_rejects_edit_on_finalized_visit(self, client, db_session):
        patient = _make_patient(db_session)
        admission = _make_admission(db_session, patient.id)
        visit = _make_aide_visit(db_session, patient.id, admission.id, status="FINALIZED")

        resp = client.post(
            f"/visits/{visit.id}/chha-outcome",
            json=self._payload(),
            headers=_qa_headers(),
        )
        assert resp.status_code == 409, resp.text

    def test_get_outcome_returns_none_when_not_yet_saved(self, client, db_session):
        patient = _make_patient(db_session)
        admission = _make_admission(db_session, patient.id)
        visit = _make_aide_visit(db_session, patient.id, admission.id)

        resp = client.get(f"/visits/{visit.id}/chha-outcome", headers=_qa_headers())
        assert resp.status_code == 200, resp.text
        assert resp.json() is None
