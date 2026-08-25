from __future__ import annotations

import pytest

from app.models.referral import Referral
from app.models.patient import Patient


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
