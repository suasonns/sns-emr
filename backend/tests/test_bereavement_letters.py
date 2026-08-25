from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest

from app.core.security import create_access_token
from app.models.bereavement_letter_tracker import BereavementLetterTracker
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


def _make_patient(db_session, tenant_id: uuid.UUID, *, mrn_prefix: str = "BLT") -> Patient:
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"{mrn_prefix}-{uuid.uuid4().hex[:10]}",
        date_of_birth=date(1940, 3, 3),
        primary_diagnosis="Hospice bereavement letters test diagnosis",
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
                full_name="Bereavement Letters Test User",
                role=role,
                active=True,
            )
        )
        db_session.commit()


@pytest.mark.integration
class TestBereavementLettersApi:
    def test_create_seeds_13_month_schedule_from_date_of_death(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id)

        response = client.post(
            "/bereavement-letters",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(patient.id), "date_of_death": "2026-01-01", "risk_level": "LOW"},
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["status"] == "ACTIVE"
        assert body["date_of_death"] == "2026-01-01"

        # 7 required baseline touchpoints + 3 optional (unincluded) = 10.
        assert body["summary"]["total_items"] == 10
        assert body["summary"]["active_items"] == 7
        assert body["summary"]["sent_count"] == 0
        assert body["summary"]["skipped_count"] == 3

        one_month = next(i for i in body["items"] if i["month_offset_days"] == 30)
        assert one_month["due_date"] == "2026-01-31"
        assert one_month["status"] == "OVERDUE"  # far in the past relative to "today" in tests

        stored = db_session.get(BereavementLetterTracker, uuid.UUID(body["id"]))
        assert stored is not None
        assert len(stored.items) == 10

    def test_create_high_risk_adds_extra_early_touchpoints(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="BLT2")

        response = client.post(
            "/bereavement-letters",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(patient.id), "date_of_death": "2026-01-01", "risk_level": "HIGH"},
        )
        assert response.status_code == 201, response.text
        body = response.json()
        # 3 high-risk extras + 7 baseline required + 3 optional = 13.
        assert body["summary"]["total_items"] == 13
        assert body["summary"]["active_items"] == 10

    def test_create_inherits_date_of_death_and_risk_from_linked_poc(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="BLT3")

        poc_resp = client.post(
            "/bereavement-poc",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(patient.id), "date_of_death": "2026-03-01", "risk_level": "MODERATE"},
        )
        assert poc_resp.status_code == 201, poc_resp.text
        poc_id = poc_resp.json()["id"]

        response = client.post(
            "/bereavement-letters",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(patient.id), "bereavement_poc_id": poc_id},
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["date_of_death"] == "2026-03-01"
        assert body["risk_level"] == "MODERATE"
        assert body["bereavement_poc_id"] == poc_id

    def test_rejects_link_to_poc_from_other_patient(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="BLT4")
        other_patient = _make_patient(db_session, tenant_id, mrn_prefix="BLT5")

        poc_resp = client.post(
            "/bereavement-poc",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(other_patient.id)},
        )
        poc_id = poc_resp.json()["id"]

        response = client.post(
            "/bereavement-letters",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(patient.id), "bereavement_poc_id": poc_id},
        )
        assert response.status_code == 404

    def test_mark_item_sent_and_unsent(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="BLT6")

        create_resp = client.post(
            "/bereavement-letters",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(patient.id), "date_of_death": "2026-01-01", "risk_level": "LOW"},
        )
        tracker_id = create_resp.json()["id"]
        item_key = next(i["key"] for i in create_resp.json()["items"] if i["month_offset_days"] == 7)

        sent_resp = client.patch(
            f"/bereavement-letters/{tracker_id}/items/{item_key}",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"sent_date": "2026-01-08", "sent_method": "MAIL", "notes": "Sympathy card mailed."},
        )
        assert sent_resp.status_code == 200, sent_resp.text
        body = sent_resp.json()
        item = next(i for i in body["items"] if i["key"] == item_key)
        assert item["status"] == "SENT"
        assert item["sent_date"] == "2026-01-08"
        assert item["sent_method"] == "MAIL"
        assert item["sent_by"] == str(TEST_USER_ID)
        assert body["summary"]["sent_count"] == 1

        unsent_resp = client.patch(
            f"/bereavement-letters/{tracker_id}/items/{item_key}",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"clear_sent": True},
        )
        assert unsent_resp.status_code == 200, unsent_resp.text
        item2 = next(i for i in unsent_resp.json()["items"] if i["key"] == item_key)
        assert item2["sent_date"] is None
        assert item2["sent_by"] is None

    def test_rejects_invalid_sent_method(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="BLT7")

        create_resp = client.post(
            "/bereavement-letters",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(patient.id), "date_of_death": "2026-01-01"},
        )
        item_key = create_resp.json()["items"][0]["key"]
        tracker_id = create_resp.json()["id"]

        response = client.patch(
            f"/bereavement-letters/{tracker_id}/items/{item_key}",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"sent_date": "2026-01-08", "sent_method": "CARRIER_PIGEON"},
        )
        assert response.status_code == 400

    def test_completing_all_active_items_auto_completes_tracker(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="BLT8")

        create_resp = client.post(
            "/bereavement-letters",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(patient.id), "date_of_death": "2026-01-01", "risk_level": "LOW"},
        )
        tracker_id = create_resp.json()["id"]
        active_keys = [i["key"] for i in create_resp.json()["items"] if i["included"]]
        assert len(active_keys) == 7

        headers = _headers(TEST_USER_ID, "MSW", tenant_id)
        body = None
        for key in active_keys:
            resp = client.patch(
                f"/bereavement-letters/{tracker_id}/items/{key}",
                headers=headers,
                json={"sent_date": "2026-01-08", "sent_method": "MAIL"},
            )
            assert resp.status_code == 200
            body = resp.json()

        assert body["status"] == "COMPLETE"
        assert body["summary"]["complete"] is True

    def test_discontinue_tracker_stops_alerts(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="BLT9")

        create_resp = client.post(
            "/bereavement-letters",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(patient.id), "date_of_death": "2026-01-01", "risk_level": "LOW"},
        )
        tracker_id = create_resp.json()["id"]
        headers = _headers(TEST_USER_ID, "MSW", tenant_id)

        alerts_before = client.get("/bereavement-letters/alerts/overdue", headers=headers)
        assert alerts_before.status_code == 200
        assert alerts_before.json()["overdue_count"] > 0

        discontinue_resp = client.patch(
            f"/bereavement-letters/{tracker_id}",
            headers=headers,
            json={"status": "DISCONTINUED", "discontinued_reason": "Family requested no further contact."},
        )
        assert discontinue_resp.status_code == 200, discontinue_resp.text
        assert discontinue_resp.json()["status"] == "DISCONTINUED"
        assert discontinue_resp.json()["discontinued_by"] == str(TEST_USER_ID)

        alerts_after = client.get("/bereavement-letters/alerts/overdue", headers=headers)
        assert alerts_after.status_code == 200
        assert alerts_after.json()["overdue_count"] == 0

    def test_resync_schedule_preserves_completed_items(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="BLT10")
        headers = _headers(TEST_USER_ID, "MSW", tenant_id)

        create_resp = client.post(
            "/bereavement-letters",
            headers=headers,
            json={"patient_id": str(patient.id), "date_of_death": "2026-01-01", "risk_level": "LOW"},
        )
        tracker_id = create_resp.json()["id"]
        first_key = create_resp.json()["items"][0]["key"]

        client.patch(
            f"/bereavement-letters/{tracker_id}/items/{first_key}",
            headers=headers,
            json={"sent_date": "2026-01-03", "sent_method": "MAIL"},
        )

        # Risk escalates to HIGH after a post-death reassessment -- resync
        # should add the extra early touchpoints without losing the
        # already-sent sympathy card.
        resync_resp = client.patch(
            f"/bereavement-letters/{tracker_id}",
            headers=headers,
            json={"risk_level": "HIGH", "resync_schedule": True},
        )
        assert resync_resp.status_code == 200, resync_resp.text
        body = resync_resp.json()
        assert body["summary"]["total_items"] == 13
        item = next(i for i in body["items"] if i["key"] == first_key)
        assert item["sent_date"] == "2026-01-03"

    def test_alerts_respects_care_team_scoping(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="BLT11")

        client.post(
            "/bereavement-letters",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={"patient_id": str(patient.id), "date_of_death": "2026-01-01", "risk_level": "LOW"},
        )

        response = client.get(
            "/bereavement-letters/alerts/overdue",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["overdue_count"] > 0
        assert all(e["patient_id"] == str(patient.id) for e in body["overdue"])

    def test_list_for_patient(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID, role="MSW")
        patient = _make_patient(db_session, tenant_id, mrn_prefix="BLT12")
        other_patient = _make_patient(db_session, tenant_id, mrn_prefix="BLT13")
        headers = _headers(TEST_USER_ID, "MSW", tenant_id)

        client.post("/bereavement-letters", headers=headers, json={"patient_id": str(patient.id)})
        client.post("/bereavement-letters", headers=headers, json={"patient_id": str(other_patient.id)})

        response = client.get(f"/bereavement-letters/patient/{patient.id}", headers=headers)
        assert response.status_code == 200, response.text
        results = response.json()
        assert len(results) == 1
        assert results[0]["patient_id"] == str(patient.id)
