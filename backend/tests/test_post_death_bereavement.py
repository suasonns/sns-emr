from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.core.security import create_access_token
from app.models.patient import Patient
from app.models.post_death_bereavement_assessment import PostDeathBereavementAssessment
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


def _make_patient(db_session, tenant_id: uuid.UUID, *, mrn_prefix: str = "PDBA") -> Patient:
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"{mrn_prefix}-{uuid.uuid4().hex[:10]}",
        date_of_birth=date(1940, 3, 3),
        primary_diagnosis="Hospice post-death bereavement test diagnosis",
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
                full_name="Post-Death Bereavement Test User",
                role=role,
                active=True,
            )
        )
        db_session.commit()


@pytest.mark.integration
class TestPostDeathBereavementApi:
    def test_create_standalone_scores_risk_from_items(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id)

        response = client.post(
            "/post-death-bereavement",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={
                "patient_id": str(patient.id),
                "date_of_death": "2026-01-01",
                "risk_items": {"suicide_ideation": {"checked": True}},
            },
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["status"] == "DRAFT"
        assert body["risk_level"] == "HIGH"
        assert body["risk_total_score"] > 0
        assert len(body["goals"]) > 0
        assert len(body["interventions"]) > 0

        stored = db_session.get(PostDeathBereavementAssessment, uuid.UUID(body["id"]))
        assert stored is not None
        assert stored.risk_level == "HIGH"

    def test_create_defaults_low_risk_when_no_items_checked(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="PDBA2")

        response = client.post(
            "/post-death-bereavement",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(patient.id)},
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["risk_level"] == "LOW"
        assert body["risk_total_score"] == 0
        assert len(body["goals"]) == 2
        assert len(body["interventions"]) == 5

    def test_inherits_primary_bereaved_from_linked_assessment(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="PDBA3")

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

        response = client.post(
            "/post-death-bereavement",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(patient.id), "bereavement_assessment_id": assessment_id},
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["primary_first_name"] == "Birdie"
        assert body["primary_last_name"] == "Ludy"
        assert body["primary_relationship_to_patient"] == "daughter"
        assert body["primary_home_phone"] == "(951) 805-6945"
        assert body["bereavement_assessment_id"] == assessment_id

        # Explicit override still wins.
        response2 = client.post(
            "/post-death-bereavement",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={
                "patient_id": str(patient.id),
                "bereavement_assessment_id": assessment_id,
                "primary_first_name": "Override",
            },
        )
        assert response2.json()["primary_first_name"] == "Override"
        assert response2.json()["primary_last_name"] == "Ludy"

    def test_inherits_primary_bereaved_from_linked_poc_when_no_assessment(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="PDBA4")

        poc_resp = client.post(
            "/bereavement-poc",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={
                "patient_id": str(patient.id),
                "primary_first_name": "Wanda",
                "primary_last_name": "Maxoff",
                "primary_relationship_to_patient": "spouse",
            },
        )
        assert poc_resp.status_code == 201, poc_resp.text
        poc_id = poc_resp.json()["id"]

        response = client.post(
            "/post-death-bereavement",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(patient.id), "bereavement_poc_id": poc_id},
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["primary_first_name"] == "Wanda"
        assert body["primary_last_name"] == "Maxoff"
        assert body["primary_relationship_to_patient"] == "spouse"
        assert body["bereavement_poc_id"] == poc_id

    def test_rejects_link_to_assessment_from_other_patient(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="PDBA5")
        other_patient = _make_patient(db_session, tenant_id, mrn_prefix="PDBA6")

        assessment_resp = client.post(
            "/bereavement-assessments",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(other_patient.id), "risk_items": {}},
        )
        assessment_id = assessment_resp.json()["id"]

        response = client.post(
            "/post-death-bereavement",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(patient.id), "bereavement_assessment_id": assessment_id},
        )
        assert response.status_code == 404

    def test_update_death_facts_and_condolence_call(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="PDBA7")

        create_resp = client.post(
            "/post-death-bereavement",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(patient.id)},
        )
        record_id = create_resp.json()["id"]

        update_resp = client.patch(
            f"/post-death-bereavement/{record_id}",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={
                "date_of_death": "2026-02-14",
                "place_of_death": "HOME",
                "death_expected": True,
                "family_present_at_death": True,
                "condolence_call_date": "2026-02-16",
                "condolence_call_by": str(TEST_USER_ID),
                "condolence_call_notes": "Spoke with daughter; coping well, declined additional support at this time.",
                "risk_items": {"suicide_ideation": {"checked": True}},
            },
        )
        assert update_resp.status_code == 200, update_resp.text
        body = update_resp.json()
        assert body["date_of_death"] == "2026-02-14"
        assert body["place_of_death"] == "HOME"
        assert body["death_expected"] is True
        assert body["family_present_at_death"] is True
        assert body["condolence_call_date"] == "2026-02-16"
        assert body["condolence_call_by"] == str(TEST_USER_ID)
        assert body["risk_level"] == "HIGH"

    def test_list_for_patient(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="PDBA8")
        other_patient = _make_patient(db_session, tenant_id, mrn_prefix="PDBA9")

        client.post(
            "/post-death-bereavement",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(patient.id)},
        )
        client.post(
            "/post-death-bereavement",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(other_patient.id)},
        )

        response = client.get(
            f"/post-death-bereavement/patient/{patient.id}",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
        )
        assert response.status_code == 200, response.text
        results = response.json()
        assert len(results) == 1
        assert results[0]["patient_id"] == str(patient.id)

    def test_sign_locks_from_further_edits(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="PDBA10")

        create_resp = client.post(
            "/post-death-bereavement",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(patient.id)},
        )
        record_id = create_resp.json()["id"]

        sign_resp = client.post(
            f"/post-death-bereavement/{record_id}/sign",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
        )
        assert sign_resp.status_code == 200, sign_resp.text
        assert sign_resp.json()["status"] == "SIGNED"
        assert sign_resp.json()["signed_by"] == str(TEST_USER_ID)

        second_sign_resp = client.post(
            f"/post-death-bereavement/{record_id}/sign",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
        )
        assert second_sign_resp.status_code == 409

        locked_resp = client.patch(
            f"/post-death-bereavement/{record_id}",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"narrative": "Should be rejected."},
        )
        assert locked_resp.status_code == 409
