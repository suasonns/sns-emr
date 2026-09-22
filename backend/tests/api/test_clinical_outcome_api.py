from __future__ import annotations

"""
API-level acceptance tests for the Clinical Outcome API (issue #143 API
phase): authentication, tenant isolation, server-derived actor identity/
discipline, primary create/read/mutate flows, closure gating, and
correction/reopen via HTTP.
"""

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from app.core.security import create_access_token
from app.models.admission import Admission
from app.models.patient import Patient
from app.models.user import User
from app.services import two_hour_response_service as thr_svc
from tests.conftest import TEST_USER_ID


def _headers(role: str, tenant_id, *, user_id=TEST_USER_ID) -> dict:
    token = create_access_token(
        user_id=user_id,
        role=role,
        tenant_id=uuid.UUID(str(tenant_id)),
        email=f"{role.lower()}-{uuid.uuid4().hex[:6]}@example.com",
    )
    return {"Authorization": f"Bearer {token}"}


def _make_user(db_session, tenant_id, *, role="RN", discipline="RN", active=True) -> User:
    user = User(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        email=f"{uuid.uuid4().hex[:10]}@example.com",
        full_name="API Test Actor",
        role=role,
        discipline=discipline,
        active=active,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _make_patient(db_session, tenant_id) -> Patient:
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        mrn=f"COAPI-{uuid.uuid4().hex[:10]}",
        date_of_birth=date(1938, 3, 4),
        primary_diagnosis="CHF",
        status="ACTIVE",
        admission_status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _make_admission(db_session, patient, tenant_id) -> Admission:
    admission = Admission(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        patient_id=patient.id,
        admission_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
        effective_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
        soc_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
        status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(admission)
    db_session.commit()
    return admission


def _make_event(db_session, patient, admission, tenant_id):
    return thr_svc.create_patient_response_event(
        db_session,
        tenant_id=uuid.UUID(str(tenant_id)),
        patient_id=patient.id,
        admission_id=admission.id,
        event_type="MEDICAL_NEED",
        received_at=datetime(2026, 11, 1, 8, 0, tzinfo=timezone.utc),
        description="Increased dyspnea reported by caregiver",
        created_by_user_id=TEST_USER_ID,
    )


def _make_outcome_fixture(db_session, tenant_id):
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id)
    event = _make_event(db_session, patient, admission, tenant_id)
    return patient, admission, event


# ---------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------


def test_unauthenticated_request_is_rejected(client, db_session):
    tenant_id = db_session.info["tenant_id"]
    patient, admission, event = _make_outcome_fixture(db_session, tenant_id)
    resp = client.post("/clinical-outcomes", json={"patient_response_event_id": str(event.id)})
    assert resp.status_code == 401


def test_unauthorized_role_is_rejected(client, db_session):
    """BILLING is a valid platform role but has no clinical-outcome authority."""
    tenant_id = db_session.info["tenant_id"]
    patient, admission, event = _make_outcome_fixture(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id, role="BILLING", discipline=None)
    headers = _headers("BILLING", tenant_id, user_id=actor.id)
    resp = client.post(
        "/clinical-outcomes", json={"patient_response_event_id": str(event.id)}, headers=headers
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------
# Create / retrieve
# ---------------------------------------------------------------------


def test_create_clinical_outcome_snapshots_account_discipline(client, db_session):
    tenant_id = db_session.info["tenant_id"]
    patient, admission, event = _make_outcome_fixture(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id, role="RN", discipline="RN")
    headers = _headers("RN", tenant_id, user_id=actor.id)

    resp = client.post(
        "/clinical-outcomes", json={"patient_response_event_id": str(event.id)}, headers=headers
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["created_by_account_discipline"] == "RN"
    assert body["created_by"] == str(actor.id)
    assert body["outcome_status"] == "IDENTIFIED"
    assert body["patient_id"] == str(patient.id)


def test_payload_discipline_field_is_ignored(client, db_session):
    """
    ClinicalOutcomeCreate has no discipline field at all -- a client trying
    to inject one in the request body can never influence the persisted
    created_by_account_discipline, which always comes from resolve_actor().
    """
    tenant_id = db_session.info["tenant_id"]
    patient, admission, event = _make_outcome_fixture(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id, role="RN", discipline="RN")
    headers = _headers("RN", tenant_id, user_id=actor.id)

    resp = client.post(
        "/clinical-outcomes",
        json={"patient_response_event_id": str(event.id), "discipline": "MD", "actor_account_discipline": "MD"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["created_by_account_discipline"] == "RN"


def test_create_from_same_source_event_is_idempotent(client, db_session):
    tenant_id = db_session.info["tenant_id"]
    patient, admission, event = _make_outcome_fixture(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id, role="RN", discipline="RN")
    headers = _headers("RN", tenant_id, user_id=actor.id)

    first = client.post(
        "/clinical-outcomes", json={"patient_response_event_id": str(event.id)}, headers=headers
    )
    second = client.post(
        "/clinical-outcomes", json={"patient_response_event_id": str(event.id)}, headers=headers
    )
    assert first.status_code == 200 and second.status_code == 200
    assert first.json()["id"] == second.json()["id"]


def test_create_rejects_unknown_source_event(client, db_session):
    tenant_id = db_session.info["tenant_id"]
    actor = _make_user(db_session, tenant_id, role="RN", discipline="RN")
    headers = _headers("RN", tenant_id, user_id=actor.id)
    resp = client.post(
        "/clinical-outcomes", json={"patient_response_event_id": str(uuid.uuid4())}, headers=headers
    )
    assert resp.status_code == 404


def test_get_and_list_clinical_outcomes(client, db_session):
    tenant_id = db_session.info["tenant_id"]
    patient, admission, event = _make_outcome_fixture(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id, role="RN", discipline="RN")
    headers = _headers("RN", tenant_id, user_id=actor.id)

    created = client.post(
        "/clinical-outcomes", json={"patient_response_event_id": str(event.id)}, headers=headers
    ).json()

    got = client.get(f"/clinical-outcomes/{created['id']}", headers=headers)
    assert got.status_code == 200
    assert got.json()["id"] == created["id"]

    listed = client.get(f"/patients/{patient.id}/clinical-outcomes", headers=headers)
    assert listed.status_code == 200
    assert any(r["id"] == created["id"] for r in listed.json())


def test_cross_tenant_outcome_access_is_rejected(client, db_session):
    tenant_id = db_session.info["tenant_id"]
    patient, admission, event = _make_outcome_fixture(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id, role="RN", discipline="RN")
    headers = _headers("RN", tenant_id, user_id=actor.id)
    created = client.post(
        "/clinical-outcomes", json={"patient_response_event_id": str(event.id)}, headers=headers
    ).json()

    other_tenant_headers = _headers("RN", uuid.uuid4(), user_id=actor.id)
    resp = client.get(f"/clinical-outcomes/{created['id']}", headers=other_tenant_headers)
    assert resp.status_code == 404


# ---------------------------------------------------------------------
# Intervention / patient response / status
# ---------------------------------------------------------------------


def test_record_intervention_does_not_resolve_outcome(client, db_session):
    tenant_id = db_session.info["tenant_id"]
    patient, admission, event = _make_outcome_fixture(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id, role="RN", discipline="RN")
    headers = _headers("RN", tenant_id, user_id=actor.id)
    created = client.post(
        "/clinical-outcomes", json={"patient_response_event_id": str(event.id)}, headers=headers
    ).json()

    resp = client.post(
        f"/clinical-outcomes/{created['id']}/interventions",
        json={"intervention_timely": True, "notes": "PRN morphine administered"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["outcome_status"] == "INTERVENTION_IN_PROGRESS"
    assert body["response_recorded_at"] is None
    assert body["closed_at"] is None


def test_persistent_response_requires_remaining_need(client, db_session):
    tenant_id = db_session.info["tenant_id"]
    patient, admission, event = _make_outcome_fixture(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id, role="RN", discipline="RN")
    headers = _headers("RN", tenant_id, user_id=actor.id)
    created = client.post(
        "/clinical-outcomes", json={"patient_response_event_id": str(event.id)}, headers=headers
    ).json()

    resp = client.post(
        f"/clinical-outcomes/{created['id']}/patient-response",
        json={
            "patient_response_status": "PERSISTENT",
            "response_recorded_at": datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc).isoformat(),
            "remaining_need_identified": False,
        },
        headers=headers,
    )
    assert resp.status_code == 422


def test_finalize_requires_patient_response_first(client, db_session):
    tenant_id = db_session.info["tenant_id"]
    patient, admission, event = _make_outcome_fixture(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id, role="RN", discipline="RN")
    headers = _headers("RN", tenant_id, user_id=actor.id)
    created = client.post(
        "/clinical-outcomes", json={"patient_response_event_id": str(event.id)}, headers=headers
    ).json()

    resp = client.post(f"/clinical-outcomes/{created['id']}/finalize", json={}, headers=headers)
    assert resp.status_code == 409


def test_finalize_then_reopen_preserves_response(client, db_session):
    tenant_id = db_session.info["tenant_id"]
    patient, admission, event = _make_outcome_fixture(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id, role="RN", discipline="RN")
    headers = _headers("RN", tenant_id, user_id=actor.id)
    created = client.post(
        "/clinical-outcomes", json={"patient_response_event_id": str(event.id)}, headers=headers
    ).json()

    resp_at = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc).isoformat()
    client.post(
        f"/clinical-outcomes/{created['id']}/patient-response",
        json={
            "patient_response_status": "IMPROVED",
            "response_recorded_at": resp_at,
            "remaining_need_identified": False,
        },
        headers=headers,
    )

    finalize_resp = client.post(f"/clinical-outcomes/{created['id']}/finalize", json={}, headers=headers)
    assert finalize_resp.status_code == 200, finalize_resp.text
    assert finalize_resp.json()["closed_at"] is not None

    # Finalized record rejects direct correction.
    correct_resp = client.post(
        f"/clinical-outcomes/{created['id']}/correct",
        json={"corrections": {"notes": "late edit"}, "correction_reason": "typo"},
        headers=headers,
    )
    assert correct_resp.status_code == 409

    reopen_resp = client.post(
        f"/clinical-outcomes/{created['id']}/reopen",
        json={"reopen_reason": "IDG requested re-review"},
        headers=headers,
    )
    assert reopen_resp.status_code == 200, reopen_resp.text
    reopened = reopen_resp.json()
    assert reopened["closed_at"] is None
    assert reopened["response_recorded_at"] == resp_at
    assert reopened["reopen_reason"] == "IDG requested re-review"


def test_correct_outcome_requires_reason_and_creates_audit_event(client, db_session):
    tenant_id = db_session.info["tenant_id"]
    patient, admission, event = _make_outcome_fixture(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id, role="RN", discipline="RN")
    headers = _headers("RN", tenant_id, user_id=actor.id)
    created = client.post(
        "/clinical-outcomes", json={"patient_response_event_id": str(event.id)}, headers=headers
    ).json()

    missing_reason = client.post(
        f"/clinical-outcomes/{created['id']}/correct",
        json={"corrections": {"notes": "corrected"}, "correction_reason": ""},
        headers=headers,
    )
    assert missing_reason.status_code == 409

    ok = client.post(
        f"/clinical-outcomes/{created['id']}/correct",
        json={"corrections": {"notes": "corrected"}, "correction_reason": "clerical error"},
        headers=headers,
    )
    assert ok.status_code == 200
    assert ok.json()["notes"] == "corrected"

    audit = client.get(f"/clinical-outcomes/{created['id']}/audit", headers=headers)
    assert audit.status_code == 200
    event_types = [row["event_type"] for row in audit.json()]
    assert "OUTCOME_CREATED" in event_types
    assert "OUTCOME_CORRECTED" in event_types
