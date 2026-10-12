from __future__ import annotations

import uuid
from datetime import date

from app.models.body_systems import BodySystemsAssessment, SystemAssessment
from app.models.patient import Patient
from app.models.rnica_assessment import RnicaAssessment
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


def _make_rnica_assessment(db_session, patient, tenant_id, *, status="DRAFT"):
    record = RnicaAssessment(
        id=uuid.uuid4(),
        patient_id=patient.id,
        tenant_id=tenant_id,
        assessment_type="RNICA",
        status=status,
    )
    db_session.add(record)
    db_session.commit()
    return record


# The 5 product-owner-authorized fields that are unconditionally required
# by `get_missing_product_authorized_requirements` regardless of
# situation -- see respiratory_product_requirements.py. Values chosen
# deliberately avoid triggering any further conditional requirement (e.g.
# `assessmentContext="UNABLE_TO_FULLY_ASSESS"` would additionally require
# `comfortFunctionImpact`), so tests that only care about some other
# behavior can merge this in without chasing a cascade of unrelated gaps.
_BASE_ALWAYS_REQUIRED_RESPIRATORY_FIELDS = {
    "assessmentContext": "NO_CURRENT_RESPIRATORY_CONCERN",
    "clinicalComparison": "COMPARISON_UNAVAILABLE",
    "oxygenUse": "NO",
    "coughType": "None",
    "respiratorySupportStatus": "NONE",
}


def _url(assessment_id) -> str:
    return f"/visits/body-systems/rnica/{assessment_id}/respiratory"


class TestGetCurrentRespiratoryAssessment:
    def test_creates_draft_on_first_access(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        rnica = _make_rnica_assessment(db_session, patient, uuid.UUID(tenant.id))

        response = client.get(_url(rnica.id), headers=rn_headers)

        assert response.status_code == 200
        body = response.json()
        assert body["system"] == "respiratory"
        assert body["situation"] is None
        assert body["reviewState"] == "not_reviewed"
        assert body["data"] == {}
        assert body["openReviewExceptions"] == []
        assert body["version"] == 1
        assert body["rnicaAssessmentId"] == str(rnica.id)

    def test_returns_same_draft_on_second_access(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        rnica = _make_rnica_assessment(db_session, patient, uuid.UUID(tenant.id))

        first = client.get(_url(rnica.id), headers=rn_headers).json()
        second = client.get(_url(rnica.id), headers=rn_headers).json()

        assert first["id"] == second["id"]
        assert first["bodySystemsAssessmentId"] == second["bodySystemsAssessmentId"]

    def test_unknown_assessment_returns_404(self, client, rn_headers):
        response = client.get(_url(uuid.uuid4()), headers=rn_headers)
        assert response.status_code == 404

    def test_two_episodes_for_same_patient_have_independent_records(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        episode_one = _make_rnica_assessment(db_session, patient, uuid.UUID(tenant.id))
        episode_two = _make_rnica_assessment(db_session, patient, uuid.UUID(tenant.id))

        client.put(_url(episode_one.id), headers=rn_headers, json={"data": {"dyspnea": "episode-one"}})
        client.put(_url(episode_two.id), headers=rn_headers, json={"data": {"dyspnea": "episode-two"}})

        one = client.get(_url(episode_one.id), headers=rn_headers).json()
        two = client.get(_url(episode_two.id), headers=rn_headers).json()

        assert one["bodySystemsAssessmentId"] != two["bodySystemsAssessmentId"]
        assert one["data"] == {"dyspnea": "episode-one"}
        assert two["data"] == {"dyspnea": "episode-two"}


class TestSaveRespiratoryDraft:
    def test_saves_situation_data_and_exceptions(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        rnica = _make_rnica_assessment(db_session, patient, uuid.UUID(tenant.id))
        client.get(_url(rnica.id), headers=rn_headers)

        response = client.put(
            _url(rnica.id),
            headers=rn_headers,
            json={
                "situation": "unable_to_assess",
                "data": {
                    "respiratoryUnableToAssess": True,
                    "respiratoryUnableToAssessReason": "Patient declined",
                    **_BASE_ALWAYS_REQUIRED_RESPIRATORY_FIELDS,
                },
                "reviewState": "reviewed_with_exception",
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
        assert body["data"]["respiratoryUnableToAssessReason"] == "Patient declined"
        assert body["version"] == 2
        assert len(body["openReviewExceptions"]) == 1
        assert body["openReviewExceptions"][0]["blockingLevel"] == "record_blocking"

    def test_rejects_invalid_situation(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        rnica = _make_rnica_assessment(db_session, patient, uuid.UUID(tenant.id))

        response = client.put(
            _url(rnica.id),
            headers=rn_headers,
            json={"situation": "not_a_real_situation", "data": {}},
        )
        assert response.status_code == 422

    def test_stale_version_is_rejected(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        rnica = _make_rnica_assessment(db_session, patient, uuid.UUID(tenant.id))
        current = client.get(_url(rnica.id), headers=rn_headers).json()
        assert current["version"] == 1

        # First save succeeds and bumps the version to 2.
        client.put(
            _url(rnica.id),
            headers=rn_headers,
            json={"data": {"dyspnea": "none"}, "expectedVersion": 1},
        )

        # Retrying with the now-stale version 1 must be rejected.
        stale_retry = client.put(
            _url(rnica.id),
            headers=rn_headers,
            json={"data": {"dyspnea": "mild"}, "expectedVersion": 1},
        )
        assert stale_retry.status_code == 409

    def test_locked_rnica_assessment_rejects_save(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        rnica = _make_rnica_assessment(db_session, patient, uuid.UUID(tenant.id), status="LOCKED")

        response = client.put(
            _url(rnica.id),
            headers=rn_headers,
            json={"data": {"dyspnea": "none"}},
        )
        assert response.status_code == 409

    def test_completion_is_rejected_without_backing_data(self, client, db_session, rn_headers, tenant):
        """Server-side anti-forgery: a client cannot reach REVIEWED merely
        by sending that string -- the data must actually back it up. This
        proves completion safety does not rely solely on the frontend."""
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        rnica = _make_rnica_assessment(db_session, patient, uuid.UUID(tenant.id))

        response = client.put(
            _url(rnica.id),
            headers=rn_headers,
            json={"situation": "new_or_worsening", "data": {}, "reviewState": "reviewed"},
        )
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert "current_finding_or_change" in detail["missingRequirements"]
        assert "intervention_or_response" in detail["missingRequirements"]

    def test_completion_is_rejected_without_a_situation(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        rnica = _make_rnica_assessment(db_session, patient, uuid.UUID(tenant.id))

        response = client.put(
            _url(rnica.id),
            headers=rn_headers,
            json={"situation": None, "data": {}, "reviewState": "reviewed"},
        )
        assert response.status_code == 422

    def test_completion_succeeds_with_backing_data(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        rnica = _make_rnica_assessment(db_session, patient, uuid.UUID(tenant.id))

        response = client.put(
            _url(rnica.id),
            headers=rn_headers,
            json={
                "situation": "new_or_worsening",
                "data": {
                    "sobSeverity": "moderate",
                    "treatmentInitiated": True,
                    **_BASE_ALWAYS_REQUIRED_RESPIRATORY_FIELDS,
                    "treatmentDecision": "INITIATED",
                    "treatmentDescription": "Bronchodilator administered per order.",
                    "clinicalResponse": "EFFECTIVE",
                    "treatmentResponseStatus": "PENDING",
                    "followUpNeed": "NOT_INDICATED",
                    "oxygenEffectivenessResponse": "Patient reports improved breathing after treatment.",
                },
                "reviewState": "reviewed",
            },
        )
        assert response.status_code == 200
        assert response.json()["reviewState"] == "reviewed"

    def test_reviewed_is_rejected_while_record_blocking_exception_is_open(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        rnica = _make_rnica_assessment(db_session, patient, uuid.UUID(tenant.id))

        response = client.put(
            _url(rnica.id),
            headers=rn_headers,
            json={
                "situation": "no_current_concern",
                "data": {"respiratoryNoCurrentConcern": True},
                "reviewState": "reviewed",
                "reviewExceptions": [
                    {"type": "unable_to_assess", "message": "x", "blockingLevel": "record_blocking"}
                ],
            },
        )
        assert response.status_code == 422

    def test_resolved_exceptions_are_not_clobbered_by_a_later_save(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        rnica = _make_rnica_assessment(db_session, patient, uuid.UUID(tenant.id))
        client.get(_url(rnica.id), headers=rn_headers)

        client.put(
            _url(rnica.id),
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
            .filter(BodySystemsAssessment.rnica_assessment_id == rnica.id)
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
            _url(rnica.id),
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
