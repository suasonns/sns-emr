from __future__ import annotations

import uuid
from datetime import date

from app.models.body_systems import BodySystemsAssessment, SystemAssessment
from app.models.patient import Patient
from app.models.tenant import Tenant
from app.models.user import User
from tests.conftest import TEST_USER_ID, _test_tenant_id


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

    def test_saves_and_returns_unable_to_assess_limitation_fields(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        client.get(f"/visits/body-systems/patients/{patient.id}/respiratory", headers=rn_headers)

        response = client.put(
            f"/visits/body-systems/patients/{patient.id}/respiratory",
            headers=rn_headers,
            json={
                "situation": "unable_to_assess",
                "data": {},
                "limitationScope": ["dyspnea", "lung_sounds"],
                "limitationReason": "Patient declined exam",
                "limitationAssessedPortion": "Visual observation only",
                "limitationFollowUpRequired": True,
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["limitationScope"] == ["dyspnea", "lung_sounds"]
        assert body["limitationReason"] == "Patient declined exam"
        assert body["limitationAssessedPortion"] == "Visual observation only"
        assert body["limitationFollowUpRequired"] is True

        # The persisted read-back (GET) must match the save response exactly.
        reloaded = client.get(f"/visits/body-systems/patients/{patient.id}/respiratory", headers=rn_headers).json()
        assert reloaded["limitationScope"] == ["dyspnea", "lung_sounds"]
        assert reloaded["limitationReason"] == "Patient declined exam"
        assert reloaded["limitationFollowUpRequired"] is True

    def test_limitation_fields_default_to_none_when_not_sent(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))

        response = client.put(
            f"/visits/body-systems/patients/{patient.id}/respiratory",
            headers=rn_headers,
            json={"situation": "stable_existing", "data": {"dyspnea": "none"}},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["limitationScope"] is None
        assert body["limitationReason"] is None
        assert body["limitationAssessedPortion"] is None
        assert body["limitationFollowUpRequired"] is None

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


class TestLimitationResponsibleClinicianAndTiming:
    """Phase F1: closes the two BACKEND_DESTINATION_MISSING limitation
    sub-fields (responsibleClinicianId, timingOrContingency) identified in
    respiratoryPersistenceMapping.ts. See migration c3b1d9e0f4a7.
    """

    def test_persists_and_round_trips_responsible_clinician_and_timing(
        self, client, db_session, rn_headers, tenant
    ):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        client.get(f"/visits/body-systems/patients/{patient.id}/respiratory", headers=rn_headers)

        response = client.put(
            f"/visits/body-systems/patients/{patient.id}/respiratory",
            headers=rn_headers,
            json={
                "situation": "unable_to_assess",
                "data": {},
                "limitationFollowUpRequired": True,
                "limitationResponsibleClinicianId": str(TEST_USER_ID),
                "limitationTimingOrContingency": "Reassess at next scheduled visit in 48 hours.",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["limitationResponsibleClinicianId"] == str(TEST_USER_ID)
        assert body["limitationTimingOrContingency"] == "Reassess at next scheduled visit in 48 hours."

        # The persisted read-back (GET) must match the save response exactly.
        reloaded = client.get(f"/visits/body-systems/patients/{patient.id}/respiratory", headers=rn_headers).json()
        assert reloaded["limitationResponsibleClinicianId"] == str(TEST_USER_ID)
        assert reloaded["limitationTimingOrContingency"] == "Reassess at next scheduled visit in 48 hours."

    def test_fields_default_to_none_when_not_sent(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))

        response = client.put(
            f"/visits/body-systems/patients/{patient.id}/respiratory",
            headers=rn_headers,
            json={"situation": "stable_existing", "data": {"dyspnea": "none"}},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["limitationResponsibleClinicianId"] is None
        assert body["limitationTimingOrContingency"] is None

    def test_malformed_clinician_id_is_rejected(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))

        response = client.put(
            f"/visits/body-systems/patients/{patient.id}/respiratory",
            headers=rn_headers,
            json={"data": {}, "limitationResponsibleClinicianId": "not-a-uuid"},
        )
        assert response.status_code == 422

    def test_unknown_clinician_id_is_rejected(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))

        response = client.put(
            f"/visits/body-systems/patients/{patient.id}/respiratory",
            headers=rn_headers,
            json={"data": {}, "limitationResponsibleClinicianId": str(uuid.uuid4())},
        )
        assert response.status_code == 422

    def test_cross_tenant_clinician_id_is_rejected(self, client, db_session, rn_headers, tenant):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))

        other_tenant_id = uuid.uuid4()
        other_tenant = db_session.get(Tenant, str(other_tenant_id))
        if other_tenant is None:
            db_session.add(
                Tenant(
                    id=str(other_tenant_id),
                    legal_name="Other Hospice",
                    display_name="Other Hospice",
                    npi="9876543210",
                    tenant_type="DEV",
                    status="ACTIVE",
                )
            )
            db_session.commit()
        other_tenant_user_id = uuid.uuid4()
        db_session.add(
            User(
                id=other_tenant_user_id,
                tenant_id=other_tenant_id,
                email=f"other-{other_tenant_user_id}@sns.local",
                full_name="Other Tenant Clinician",
                role="RN",
                active=True,
            )
        )
        db_session.commit()

        response = client.put(
            f"/visits/body-systems/patients/{patient.id}/respiratory",
            headers=rn_headers,
            json={"data": {}, "limitationResponsibleClinicianId": str(other_tenant_user_id)},
        )
        assert response.status_code == 422

    def test_stale_version_still_rejected_even_with_valid_clinician(
        self, client, db_session, rn_headers, tenant
    ):
        patient = _make_patient(db_session, uuid.UUID(tenant.id))
        current = client.get(f"/visits/body-systems/patients/{patient.id}/respiratory", headers=rn_headers).json()
        assert current["version"] == 1

        client.put(
            f"/visits/body-systems/patients/{patient.id}/respiratory",
            headers=rn_headers,
            json={"data": {"dyspnea": "none"}, "expectedVersion": 1},
        )

        stale_retry = client.put(
            f"/visits/body-systems/patients/{patient.id}/respiratory",
            headers=rn_headers,
            json={
                "data": {"dyspnea": "mild"},
                "expectedVersion": 1,
                "limitationResponsibleClinicianId": str(TEST_USER_ID),
            },
        )
        assert stale_retry.status_code == 409
