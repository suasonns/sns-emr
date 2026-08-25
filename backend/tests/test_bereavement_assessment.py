from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.core.security import create_access_token
from app.models.bereavement_assessment import BereavementAssessment
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


def _make_patient(db_session, tenant_id: uuid.UUID, *, mrn_prefix: str = "BRVMT") -> Patient:
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"{mrn_prefix}-{uuid.uuid4().hex[:10]}",
        date_of_birth=date(1940, 3, 3),
        primary_diagnosis="Hospice bereavement test diagnosis",
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
                full_name="Bereavement Test User",
                role=role,
                active=True,
            )
        )
        db_session.commit()


RISK_ITEMS_LOW = {
    "preexisting_health_concerns": {"checked": True, "note": None},
}

RISK_ITEMS_HIGH_SUICIDE = {
    "suicide_ideation": {"checked": True, "note": None},
}

RISK_ITEMS_MODERATE = {
    "substance_abuse": {"checked": True, "note": None},
    "mental_health_history": {"checked": True, "note": None},
    "extreme_dependency": {"checked": True, "note": None},
}


@pytest.mark.integration
class TestBereavementAssessmentApi:
    def test_create_assessment_computes_low_risk(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id)

        response = client.post(
            "/bereavement-assessments",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={
                "patient_id": str(patient.id),
                "discipline": "BSW",
                "primary_first_name": "Birdie",
                "primary_last_name": "Ludy",
                "primary_relationship_to_patient": "daughter",
                "risk_items": RISK_ITEMS_LOW,
            },
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["status"] == "DRAFT"
        assert body["risk_total_score"] == 1
        assert body["risk_level"] == "LOW"

        stored = db_session.get(BereavementAssessment, uuid.UUID(body["id"]))
        assert stored is not None
        assert stored.risk_level == "LOW"

    def test_moderate_risk_totals_across_multiple_two_point_items(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="BRVMT2")

        response = client.post(
            "/bereavement-assessments",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={
                "patient_id": str(patient.id),
                "risk_items": RISK_ITEMS_MODERATE,
            },
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["risk_total_score"] == 6
        assert body["risk_level"] == "MODERATE"

    def test_suicide_ideation_forces_high_risk_regardless_of_total(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="BRVMT3")

        response = client.post(
            "/bereavement-assessments",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={
                "patient_id": str(patient.id),
                "risk_items": RISK_ITEMS_HIGH_SUICIDE,
            },
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["risk_total_score"] == 10
        assert body["risk_level"] == "HIGH"

    def test_list_assessments_for_patient(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="BRVMT4")
        other_patient = _make_patient(db_session, tenant_id, mrn_prefix="BRVMT5")

        client.post(
            "/bereavement-assessments",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(patient.id), "risk_items": RISK_ITEMS_LOW},
        )
        client.post(
            "/bereavement-assessments",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(other_patient.id), "risk_items": RISK_ITEMS_LOW},
        )

        response = client.get(
            f"/bereavement-assessments/patient/{patient.id}",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
        )
        assert response.status_code == 200, response.text
        results = response.json()
        assert len(results) == 1
        assert results[0]["patient_id"] == str(patient.id)

    def test_update_recomputes_risk_level(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="BRVMT6")

        create_resp = client.post(
            "/bereavement-assessments",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(patient.id), "risk_items": RISK_ITEMS_LOW},
        )
        assessment_id = create_resp.json()["id"]

        update_resp = client.patch(
            f"/bereavement-assessments/{assessment_id}",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"risk_items": RISK_ITEMS_HIGH_SUICIDE, "narrative": "Updated narrative."},
        )
        assert update_resp.status_code == 200, update_resp.text
        body = update_resp.json()
        assert body["risk_level"] == "HIGH"
        assert body["narrative"] == "Updated narrative."

    def test_sign_locks_assessment_from_further_edits(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="BRVMT7")

        create_resp = client.post(
            "/bereavement-assessments",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={
                "patient_id": str(patient.id),
                "primary_first_name": "Birdie",
                "risk_items": RISK_ITEMS_LOW,
            },
        )
        assessment_id = create_resp.json()["id"]

        sign_resp = client.post(
            f"/bereavement-assessments/{assessment_id}/sign",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
        )
        assert sign_resp.status_code == 200, sign_resp.text
        assert sign_resp.json()["status"] == "SIGNED"
        assert sign_resp.json()["signed_by"] == str(TEST_USER_ID)

        locked_update_resp = client.patch(
            f"/bereavement-assessments/{assessment_id}",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"narrative": "Should be rejected."},
        )
        assert locked_update_resp.status_code == 409
