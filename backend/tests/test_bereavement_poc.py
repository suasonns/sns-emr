from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.core.security import create_access_token
from app.models.bereavement_assessment import BereavementAssessment
from app.models.bereavement_poc import BereavementPOC
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


def _make_patient(db_session, tenant_id: uuid.UUID, *, mrn_prefix: str = "BPOC") -> Patient:
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"{mrn_prefix}-{uuid.uuid4().hex[:10]}",
        date_of_birth=date(1940, 3, 3),
        primary_diagnosis="Hospice bereavement POC test diagnosis",
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
                full_name="Bereavement POC Test User",
                role=role,
                active=True,
            )
        )
        db_session.commit()


@pytest.mark.integration
class TestBereavementPOCApi:
    def test_create_poc_defaults_low_risk_catalog_and_13_month_plan(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id)

        response = client.post(
            "/bereavement-poc",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(patient.id), "date_of_death": "2026-01-01"},
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["status"] == "DRAFT"
        assert body["risk_level"] == "LOW"
        assert body["risk_source"] == "MANUAL"
        assert body["risk_score"] is None
        assert len(body["goals"]) == 2
        assert len(body["interventions"]) == 5
        # Baseline required schedule (7) + optional clinician-opt-in
        # touchpoints (3, unincluded by default) = 10.
        assert len(body["action_plan"]) == 10
        required = [a for a in body["action_plan"] if a["required"]]
        optional = [a for a in body["action_plan"] if not a["required"]]
        assert len(required) == 7
        assert len(optional) == 3
        assert all(a["included"] is False for a in optional)
        assert body["action_plan"][0]["planned_date"] == "2026-01-08"
        assert body["action_plan"][-1]["planned_date"] == "2027-01-31"

    def test_create_poc_inherits_risk_level_from_linked_assessment(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="BPOC2")

        assessment_resp = client.post(
            "/bereavement-assessments",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(patient.id), "risk_items": {"suicide_ideation": {"checked": True}}},
        )
        assert assessment_resp.status_code == 201, assessment_resp.text
        assessment_id = assessment_resp.json()["id"]
        assert assessment_resp.json()["risk_level"] == "HIGH"

        poc_resp = client.post(
            "/bereavement-poc",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={
                "patient_id": str(patient.id),
                "bereavement_assessment_id": assessment_id,
                "date_of_death": "2026-01-01",
            },
        )
        assert poc_resp.status_code == 201, poc_resp.text
        body = poc_resp.json()
        assert body["risk_level"] == "HIGH"
        assert body["risk_source"] == "SCORED"
        assert body["risk_score"] == 10
        assert body["bereavement_assessment_id"] == assessment_id
        # HIGH risk layers 3 extra required early touchpoints onto the
        # 7-item baseline (10 required) + 3 optional = 13.
        assert len(body["action_plan"]) == 13
        assert any(item["label"] == "High-risk follow-up (48 hours)" for item in body["action_plan"])
        assert any(item["key"] == "notify_idg" for item in body["interventions"])

        stored = db_session.get(BereavementPOC, uuid.UUID(body["id"]))
        assert stored is not None
        assert stored.risk_level == "HIGH"

    def test_create_poc_inherits_primary_bereaved_from_linked_assessment(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="BPOC7")

        assessment_resp = client.post(
            "/bereavement-assessments",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={
                "patient_id": str(patient.id),
                "primary_first_name": "Birdie",
                "primary_last_name": "Ludy",
                "primary_relationship_to_patient": "daughter",
                "primary_home_phone": "(951) 805-6945",
                "risk_items": {},
            },
        )
        assert assessment_resp.status_code == 201, assessment_resp.text
        assessment_id = assessment_resp.json()["id"]

        poc_resp = client.post(
            "/bereavement-poc",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(patient.id), "bereavement_assessment_id": assessment_id},
        )
        assert poc_resp.status_code == 201, poc_resp.text
        body = poc_resp.json()
        assert body["primary_first_name"] == "Birdie"
        assert body["primary_last_name"] == "Ludy"
        assert body["primary_relationship_to_patient"] == "daughter"
        assert body["primary_home_phone"] == "(951) 805-6945"

        # Explicit fields on the POC payload override the inherited values.
        poc_resp2 = client.post(
            "/bereavement-poc",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={
                "patient_id": str(patient.id),
                "bereavement_assessment_id": assessment_id,
                "primary_first_name": "Override",
            },
        )
        assert poc_resp2.json()["primary_first_name"] == "Override"
        assert poc_resp2.json()["primary_last_name"] == "Ludy"

    def test_standalone_poc_risk_level_is_manual_until_linked(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="BPOC8")

        create_resp = client.post(
            "/bereavement-poc",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(patient.id), "risk_level": "HIGH"},
        )
        assert create_resp.status_code == 201, create_resp.text
        assert create_resp.json()["risk_level"] == "HIGH"
        assert create_resp.json()["risk_source"] == "MANUAL"
        assert create_resp.json()["risk_score"] is None

        assessment_resp = client.post(
            "/bereavement-assessments",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(patient.id), "risk_items": {"suicide_ideation": {"checked": True}}},
        )
        assessment_id = assessment_resp.json()["id"]

        link_resp = client.patch(
            f"/bereavement-poc/{create_resp.json()['id']}",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"bereavement_assessment_id": assessment_id},
        )
        assert link_resp.status_code == 200, link_resp.text
        assert link_resp.json()["risk_source"] == "SCORED"
        assert link_resp.json()["risk_score"] == 10
        assert link_resp.json()["risk_level"] == "HIGH"

    def test_update_action_plan_marks_contact_completed(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="BPOC3")

        create_resp = client.post(
            "/bereavement-poc",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(patient.id), "date_of_death": "2026-01-01"},
        )
        poc_id = create_resp.json()["id"]
        action_plan = create_resp.json()["action_plan"]
        action_plan[0]["completed_date"] = "2026-01-09"
        action_plan[0]["completed_by"] = str(TEST_USER_ID)
        action_plan[0]["notes"] = "Sympathy card mailed."

        update_resp = client.patch(
            f"/bereavement-poc/{poc_id}",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"action_plan": action_plan},
        )
        assert update_resp.status_code == 200, update_resp.text
        body = update_resp.json()
        assert body["action_plan"][0]["completed_date"] == "2026-01-09"
        assert body["action_plan"][0]["completed_by"] == str(TEST_USER_ID)
        assert body["action_plan"][0]["notes"] == "Sympathy card mailed."

    def test_list_pocs_for_patient(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="BPOC4")
        other_patient = _make_patient(db_session, tenant_id, mrn_prefix="BPOC5")

        client.post(
            "/bereavement-poc",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(patient.id)},
        )
        client.post(
            "/bereavement-poc",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(other_patient.id)},
        )

        response = client.get(
            f"/bereavement-poc/patient/{patient.id}",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
        )
        assert response.status_code == 200, response.text
        results = response.json()
        assert len(results) == 1
        assert results[0]["patient_id"] == str(patient.id)

    def test_sign_locks_poc_from_further_edits(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="BPOC6")

        create_resp = client.post(
            "/bereavement-poc",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(patient.id)},
        )
        poc_id = create_resp.json()["id"]

        sign_resp = client.post(
            f"/bereavement-poc/{poc_id}/sign",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
        )
        assert sign_resp.status_code == 200, sign_resp.text
        assert sign_resp.json()["status"] == "SIGNED"
        assert sign_resp.json()["signed_by"] == str(TEST_USER_ID)

        locked_resp = client.patch(
            f"/bereavement-poc/{poc_id}",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"narrative": "Should be rejected."},
        )
        assert locked_resp.status_code == 409
