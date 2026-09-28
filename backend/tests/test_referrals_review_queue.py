from __future__ import annotations

import uuid

import pytest

from app.core.security import create_access_token
from app.models.referral import Referral
from app.models.patient import Patient
from app.models.tenant import Tenant

TEST_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")

REFERRAL_PAYLOAD = {
    "first_name": "Pending",
    "last_name": "Review",
    "date_of_birth": "1950-01-15",
    "phone": "555-020-3030",
    "referral_source": "Sunrise SNF",
    "referral_date": "2026-08-20",
    "primary_diagnosis": "Diagnosis pending",
}


@pytest.mark.integration
def test_create_referral_lands_as_pending_with_no_patient(client, db_session, rn_headers):
    resp = client.post("/referrals", json=REFERRAL_PAYLOAD, headers=rn_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "PENDING"
    assert body["converted_patient_id"] is None

    referral = db_session.query(Referral).filter(Referral.id == body["id"]).first()
    assert referral is not None
    assert referral.status == "PENDING"

    # No patient should exist yet -- creating a referral must not create a Patient.
    assert db_session.query(Patient).filter(Patient.id == referral.id).first() is None


@pytest.mark.integration
def test_list_referrals_filters_by_status(client, rn_headers):
    client.post("/referrals", json=REFERRAL_PAYLOAD, headers=rn_headers)

    resp = client.get("/referrals", params={"status": "pending"}, headers=rn_headers)
    assert resp.status_code == 200, resp.text
    assert all(row["status"] == "PENDING" for row in resp.json())

    resp = client.get("/referrals", params={"status": "declined"}, headers=rn_headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.integration
def test_accept_referral_creates_patient_and_marks_accepted(client, db_session, rn_headers):
    create_resp = client.post("/referrals", json=REFERRAL_PAYLOAD, headers=rn_headers)
    referral_id = create_resp.json()["id"]

    accept_resp = client.post(f"/referrals/{referral_id}/accept", headers=rn_headers)
    assert accept_resp.status_code == 200, accept_resp.text
    result = accept_resp.json()
    assert result["facesheet_created"] is True

    db_session.expire_all()
    referral = db_session.query(Referral).filter(Referral.id == referral_id).first()
    assert referral.status == "ACCEPTED"
    assert str(referral.converted_patient_id) == result["id"]
    assert referral.reviewed_by is not None
    assert referral.reviewed_at is not None

    patient = db_session.query(Patient).filter(Patient.id == referral.converted_patient_id).first()
    assert patient is not None

    # Accepting an already-decided referral must be rejected.
    second_attempt = client.post(f"/referrals/{referral_id}/accept", headers=rn_headers)
    assert second_attempt.status_code == 400


@pytest.mark.integration
def test_decline_referral_requires_reason_and_creates_no_patient(client, db_session, rn_headers):
    create_resp = client.post("/referrals", json=REFERRAL_PAYLOAD, headers=rn_headers)
    referral_id = create_resp.json()["id"]

    missing_reason = client.post(f"/referrals/{referral_id}/decline", json={"reason": ""}, headers=rn_headers)
    assert missing_reason.status_code == 422

    decline_resp = client.post(
        f"/referrals/{referral_id}/decline",
        json={"reason": "Patient does not meet hospice eligibility criteria"},
        headers=rn_headers,
    )
    assert decline_resp.status_code == 200, decline_resp.text
    body = decline_resp.json()
    assert body["status"] == "DECLINED"
    assert body["decline_reason"] == "Patient does not meet hospice eligibility criteria"
    assert body["converted_patient_id"] is None

    referral = db_session.query(Referral).filter(Referral.id == referral_id).first()
    assert db_session.query(Patient).filter(Patient.id == referral.id).first() is None

    # Declining an already-decided referral must be rejected.
    second_attempt = client.post(
        f"/referrals/{referral_id}/decline",
        json={"reason": "Duplicate decline attempt"},
        headers=rn_headers,
    )
    assert second_attempt.status_code == 400


@pytest.mark.integration
def test_list_referrals_filters_by_converted_patient_id(client, db_session, rn_headers):
    """RNICA Evidence & Intake's Referral Data card reads the original
    admission referral for an already-converted patient via
    ?converted_patient_id=. Confirms it returns exactly that patient's
    referral and nothing else, without breaking existing status filtering.
    """
    create_resp = client.post("/referrals", json=REFERRAL_PAYLOAD, headers=rn_headers)
    referral_id = create_resp.json()["id"]

    accept_resp = client.post(f"/referrals/{referral_id}/accept", headers=rn_headers)
    converted_patient_id = accept_resp.json()["id"]

    resp = client.get(
        "/referrals",
        params={"converted_patient_id": converted_patient_id},
        headers=rn_headers,
    )
    assert resp.status_code == 200, resp.text
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["id"] == referral_id
    assert rows[0]["converted_patient_id"] == converted_patient_id

    # A patient id with no matching referral must return an empty list, not
    # every referral (i.e. the filter is not silently ignored).
    resp_none = client.get(
        "/referrals",
        params={"converted_patient_id": str(uuid.uuid4())},
        headers=rn_headers,
    )
    assert resp_none.status_code == 200
    assert resp_none.json() == []

    # An invalid (non-UUID) value must be rejected, not silently ignored.
    resp_invalid = client.get(
        "/referrals",
        params={"converted_patient_id": "not-a-uuid"},
        headers=rn_headers,
    )
    assert resp_invalid.status_code == 422


@pytest.mark.integration
def test_referral_converted_patient_filter_respects_tenant_isolation(client, db_session, rn_headers):
    """A referral belonging to a different tenant must never be returned by
    the converted_patient_id filter, even if the caller supplies that
    other tenant's converted patient id directly -- tenant isolation is
    enforced by the existing base query (Referral.tenant_id ==
    caller's tenant), not by the new filter alone.
    """
    other_tenant_id = uuid.uuid4()
    db_session.add(
        Tenant(
            id=other_tenant_id,
            legal_name="Other Agency (referral isolation test)",
            display_name="Other Agency",
            npi="1928374650",
        )
    )
    db_session.commit()

    other_tenant_headers = {
        "Authorization": "Bearer "
        + create_access_token(
            user_id=TEST_USER_ID,
            role="RN",
            tenant_id=other_tenant_id,
            email="other_tenant_nurse@example.com",
        )
    }

    other_referral_resp = client.post("/referrals", json=REFERRAL_PAYLOAD, headers=other_tenant_headers)
    other_referral_id = other_referral_resp.json()["id"]
    other_accept_resp = client.post(f"/referrals/{other_referral_id}/accept", headers=other_tenant_headers)
    other_converted_patient_id = other_accept_resp.json()["id"]

    # The original (default test tenant) caller must not see the other
    # tenant's referral, even when querying by its exact converted patient id.
    resp = client.get(
        "/referrals",
        params={"converted_patient_id": other_converted_patient_id},
        headers=rn_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == []
