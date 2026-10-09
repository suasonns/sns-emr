from __future__ import annotations

import uuid
from datetime import date

from app.models.body_systems import BodySystemsAssessment, SystemAssessment
from app.models.patient import Patient
from tests.conftest import _test_tenant_id


def _make_patient(db_session, tenant_id):
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"BODYSYSAPI-{uuid.uuid4().hex[:12]}",
        date_of_birth=date(1948, 3, 2),
        primary_diagnosis="Hospice qualifying diagnosis",
        status="ACTIVE",
        admission_status="PRE_REFERRAL",
        created_by=None,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


class TestGetCurrentRespiratoryAssessment:
    def test_creates_draft_on_first_access(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))

        response = client.get(f"/visits/body-systems/patients/{patient.id}/respiratory", headers=rn_headers)

        assert response.status_code == 200
        body = response.json()
        assert body["system"] == "respiratory"
        assert body["situation"] is None
        assert body["reviewState"] == "not_reviewed"
        assert body["data"] == {}
        assert body["openReviewExceptions"] == []
        assert body["version"] == 1

    def test_returns_same_draft_on_second_access(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))

        first = client.get(f"/visits/body-systems/patients/{patient.id}/respiratory", headers=rn_headers).json()
        second = client.get(f"/visits/body-systems/patients/{patient.id}/respiratory", headers=rn_headers).json()

        assert first["id"] == second["id"]
        assert first["bodySystemsAssessmentId"] == second["bodySystemsAssessmentId"]

    def test_unknown_patient_returns_404(self, client, rn_headers):
        response = client.get(f"/visits/body-systems/patients/{uuid.uuid4()}/respiratory", headers=rn_headers)
        assert response.status_code == 404


class TestSaveRespiratoryDraft:
    def test_saves_situation_data_and_exceptions(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        client.get(f"/visits/body-systems/patients/{patient.id}/respiratory", headers=rn_headers)

        response = client.put(
            f"/visits/body-systems/patients/{patient.id}/respiratory",
            headers=rn_headers,
            json={
                "situation": "unable_to_assess",
                "data": {"respiratory_overview": "Unable to Assess"},
                "reviewState": "in_progress",
                "reviewExceptions": [
                    {
                        "type": "unable_to_assess",
                        "message": "respiratory is marked unable to assess but has no documented reason.",
                        "blockingLevel": "record_blocking",
                        "fieldPath": "limitation.reason",
                    }
                ],
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["situation"] == "unable_to_assess"
        assert body["data"] == {"respiratory_overview": "Unable to Assess"}
        assert body["version"] == 2
        assert len(body["openReviewExceptions"]) == 1
        assert body["openReviewExceptions"][0]["blockingLevel"] == "record_blocking"

    def test_rejects_invalid_situation(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))

        response = client.put(
            f"/visits/body-systems/patients/{patient.id}/respiratory",
            headers=rn_headers,
            json={"situation": "not_a_real_situation", "data": {}},
        )
        assert response.status_code == 422

    def test_stale_version_is_rejected(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        current = client.get(f"/visits/body-systems/patients/{patient.id}/respiratory", headers=rn_headers).json()
        assert current["version"] == 1

        # First save succeeds and bumps the version to 2.
        client.put(
            f"/visits/body-systems/patients/{patient.id}/respiratory",
            headers=rn_headers,
            json={"data": {"dyspnea": "none"}, "expectedVersion": 1},
        )

        # Retrying with the now-stale version 1 must be rejected.
        stale_retry = client.put(
            f"/visits/body-systems/patients/{patient.id}/respiratory",
            headers=rn_headers,
            json={"data": {"dyspnea": "mild"}, "expectedVersion": 1},
        )
        assert stale_retry.status_code == 409

    def test_resolved_exceptions_are_not_clobbered_by_a_later_save(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        client.get(f"/visits/body-systems/patients/{patient.id}/respiratory", headers=rn_headers)

        client.put(
            f"/visits/body-systems/patients/{patient.id}/respiratory",
            headers=rn_headers,
            json={
                "data": {},
                "reviewExceptions": [
                    {
                        "type": "unable_to_assess",
                        "message": "missing reason",
                        "blockingLevel": "record_blocking",
                    }
                ],
            },
        )

        assessment = (
            db_session.query(BodySystemsAssessment)
            .filter(BodySystemsAssessment.patient_id == patient.id)
            .first()
        )
        system_assessment = (
            db_session.query(SystemAssessment)
            .filter(SystemAssessment.body_systems_assessment_id == assessment.id)
            .first()
        )
        from app.models.body_systems import ReviewException

        exception = (
            db_session.query(ReviewException)
            .filter(ReviewException.body_systems_assessment_id == assessment.id)
            .first()
        )
        exception.status = "resolved"
        from datetime import datetime, timezone

        exception.resolved_at = datetime.now(timezone.utc)
        db_session.commit()

        # A later save with no open exceptions must not resurrect/duplicate
        # the already-resolved one.
        response = client.put(
            f"/visits/body-systems/patients/{patient.id}/respiratory",
            headers=rn_headers,
            json={"data": {"dyspnea": "none"}, "reviewExceptions": []},
        )
        assert response.status_code == 200
        assert response.json()["openReviewExceptions"] == []

        remaining = (
            db_session.query(ReviewException)
            .filter(ReviewException.body_systems_assessment_id == assessment.id)
            .count()
        )
        assert remaining == 1  # the resolved one is still there, untouched
