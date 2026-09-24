from __future__ import annotations

"""
API-level acceptance tests for the IDG Follow-Up API (issue #143 API
phase): creation via idg-follow-ups, assignment/reassignment, progress,
patient-response linking, completion gating, and reopen -- all via HTTP,
extending the existing idg_reviews table.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.core.security import create_access_token
from app.models.patient import Patient
from app.models.user import User
from app.services import clinical_outcome_service as co_svc
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
        full_name="IDG API Test Actor",
        role=role,
        discipline=discipline,
        active=active,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _make_patient(db_session, tenant_id) -> Patient:
    from datetime import date

    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        mrn=f"IDGAPI-{uuid.uuid4().hex[:10]}",
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="CHF",
        status="ACTIVE",
        admission_status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _make_clinical_outcome(db_session, tenant_id, patient):
    from app.models.admission import Admission

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

    event = thr_svc.create_patient_response_event(
        db_session,
        tenant_id=uuid.UUID(str(tenant_id)),
        patient_id=patient.id,
        admission_id=admission.id,
        event_type="MEDICAL_NEED",
        received_at=datetime(2026, 11, 1, 8, 0, tzinfo=timezone.utc),
        description="Reported increased anxiety",
        created_by_user_id=TEST_USER_ID,
    )
    record = co_svc.create_outcome_from_patient_response_event(
        db_session, event=event, actor_user_id=TEST_USER_ID, actor_account_discipline="RN"
    )
    return record


def _create_follow_up(client, headers, patient, clinical_outcome_record_id):
    return client.post(
        "/idg-follow-ups",
        json={
            "patient_id": str(patient.id),
            "desired_patient_outcome": "Anxiety reduced to baseline",
            "follow_up_action": "MSW to assess and coordinate counseling",
            "follow_up_due_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
            "clinical_outcome_record_id": str(clinical_outcome_record_id),
        },
        headers=headers,
    )


# ---------------------------------------------------------------------
# Authentication / creation
# ---------------------------------------------------------------------


def test_unauthenticated_create_is_rejected(client, db_session):
    resp = client.post("/idg-follow-ups", json={"patient_id": str(uuid.uuid4())})
    assert resp.status_code == 401


def test_unauthorized_role_is_rejected(client, db_session):
    """BILLING is a valid platform role but has no IDG follow-up authority."""
    tenant_id = db_session.info["tenant_id"]
    patient = _make_patient(db_session, tenant_id)
    record = _make_clinical_outcome(db_session, tenant_id, patient)
    actor = _make_user(db_session, tenant_id, role="BILLING", discipline=None)
    headers = _headers("BILLING", tenant_id, user_id=actor.id)

    resp = client.post(
        "/idg-follow-ups",
        json={
            "patient_id": str(patient.id),
            "desired_patient_outcome": "Reduced anxiety",
            "follow_up_action": "assess",
            "follow_up_due_at": datetime.now(timezone.utc).isoformat(),
            "clinical_outcome_record_id": str(record.id),
        },
        headers=headers,
    )
    assert resp.status_code == 403


def test_create_requires_desired_patient_outcome(client, db_session):
    tenant_id = db_session.info["tenant_id"]
    patient = _make_patient(db_session, tenant_id)
    record = _make_clinical_outcome(db_session, tenant_id, patient)
    actor = _make_user(db_session, tenant_id, role="SW", discipline="MSW")
    headers = _headers("SW", tenant_id, user_id=actor.id)

    resp = client.post(
        "/idg-follow-ups",
        json={
            "patient_id": str(patient.id),
            "desired_patient_outcome": "",
            "follow_up_action": "assess",
            "follow_up_due_at": datetime.now(timezone.utc).isoformat(),
            "clinical_outcome_record_id": str(record.id),
        },
        headers=headers,
    )
    assert resp.status_code == 422


def test_create_idg_follow_up_snapshots_discipline_via_audit(client, db_session):
    tenant_id = db_session.info["tenant_id"]
    patient = _make_patient(db_session, tenant_id)
    record = _make_clinical_outcome(db_session, tenant_id, patient)
    actor = _make_user(db_session, tenant_id, role="SW", discipline="MSW")
    headers = _headers("SW", tenant_id, user_id=actor.id)

    resp = _create_follow_up(client, headers, patient, record.id)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["desired_patient_outcome"] == "Anxiety reduced to baseline"
    assert body["follow_up_status"] is None

    audit = client.get(f"/idg-reviews/{body['id']}/audit", headers=headers)
    assert audit.status_code == 200
    rows = audit.json()
    assert rows[0]["event_type"] == "IDG_FOLLOW_UP_CREATED"
    assert rows[0]["actor_account_discipline"] == "MSW"


def test_cross_tenant_idg_review_access_is_rejected(client, db_session):
    tenant_id = db_session.info["tenant_id"]
    patient = _make_patient(db_session, tenant_id)
    record = _make_clinical_outcome(db_session, tenant_id, patient)
    actor = _make_user(db_session, tenant_id, role="SW", discipline="MSW")
    headers = _headers("SW", tenant_id, user_id=actor.id)
    created = _create_follow_up(client, headers, patient, record.id).json()

    other_tenant_headers = _headers("SW", uuid.uuid4(), user_id=actor.id)
    resp = client.get(f"/idg-reviews/{created['id']}/follow-up", headers=other_tenant_headers)
    assert resp.status_code == 404


# ---------------------------------------------------------------------
# Assignment / progress / completion / reopen
# ---------------------------------------------------------------------


def test_assign_and_reassign_follow_up_requires_reason(client, db_session):
    tenant_id = db_session.info["tenant_id"]
    patient = _make_patient(db_session, tenant_id)
    record = _make_clinical_outcome(db_session, tenant_id, patient)
    actor = _make_user(db_session, tenant_id, role="SW", discipline="MSW")
    headers = _headers("SW", tenant_id, user_id=actor.id)
    created = _create_follow_up(client, headers, patient, record.id).json()

    assignee_one = _make_user(db_session, tenant_id, role="SW", discipline="MSW")
    assign_resp = client.post(
        f"/idg-reviews/{created['id']}/assign",
        json={"assigned_user_id": str(assignee_one.id)},
        headers=headers,
    )
    assert assign_resp.status_code == 200, assign_resp.text
    assert assign_resp.json()["follow_up_status"] == "ASSIGNED"

    assignee_two = _make_user(db_session, tenant_id, role="CHAPLAIN", discipline="CHAPLAIN")
    missing_reason = client.post(
        f"/idg-reviews/{created['id']}/reassign",
        json={"assigned_user_id": str(assignee_two.id)},
        headers=headers,
    )
    assert missing_reason.status_code == 422

    with_reason = client.post(
        f"/idg-reviews/{created['id']}/reassign",
        json={"assigned_user_id": str(assignee_two.id), "reassignment_reason": "coverage change"},
        headers=headers,
    )
    assert with_reason.status_code == 200
    assert with_reason.json()["follow_up_assigned_to_user_id"] == str(assignee_two.id)


def test_progress_does_not_complete_follow_up(client, db_session):
    tenant_id = db_session.info["tenant_id"]
    patient = _make_patient(db_session, tenant_id)
    record = _make_clinical_outcome(db_session, tenant_id, patient)
    actor = _make_user(db_session, tenant_id, role="SW", discipline="MSW")
    headers = _headers("SW", tenant_id, user_id=actor.id)
    created = _create_follow_up(client, headers, patient, record.id).json()

    resp = client.post(
        f"/idg-reviews/{created['id']}/progress",
        json={"progress_summary": "Contacted family, scheduling counseling"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["follow_up_status"] == "IN_PROGRESS"


def test_complete_requires_closure_summary_and_continuing_plan_for_remaining_need(client, db_session):
    tenant_id = db_session.info["tenant_id"]
    patient = _make_patient(db_session, tenant_id)
    record = _make_clinical_outcome(db_session, tenant_id, patient)
    actor = _make_user(db_session, tenant_id, role="SW", discipline="MSW")
    headers = _headers("SW", tenant_id, user_id=actor.id)
    created = _create_follow_up(client, headers, patient, record.id).json()

    missing_summary = client.post(
        f"/idg-reviews/{created['id']}/complete", json={"closure_summary": ""}, headers=headers
    )
    assert missing_summary.status_code == 409

    missing_plan = client.post(
        f"/idg-reviews/{created['id']}/complete",
        json={"closure_summary": "Resolved", "remaining_need": True},
        headers=headers,
    )
    assert missing_plan.status_code == 409

    ok = client.post(
        f"/idg-reviews/{created['id']}/complete",
        json={
            "closure_summary": "Resolved",
            "remaining_need": True,
            "continuing_plan": "MSW to follow up monthly",
        },
        headers=headers,
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["follow_up_status"] == "COMPLETED"


def test_reopen_completed_follow_up_requires_reason(client, db_session):
    tenant_id = db_session.info["tenant_id"]
    patient = _make_patient(db_session, tenant_id)
    record = _make_clinical_outcome(db_session, tenant_id, patient)
    actor = _make_user(db_session, tenant_id, role="SW", discipline="MSW")
    headers = _headers("SW", tenant_id, user_id=actor.id)
    created = _create_follow_up(client, headers, patient, record.id).json()
    client.post(
        f"/idg-reviews/{created['id']}/complete",
        json={"closure_summary": "Resolved"},
        headers=headers,
    )

    missing_reason = client.post(
        f"/idg-reviews/{created['id']}/reopen", json={"reopen_reason": ""}, headers=headers
    )
    assert missing_reason.status_code == 409

    ok = client.post(
        f"/idg-reviews/{created['id']}/reopen",
        json={"reopen_reason": "Family reports symptoms returned"},
        headers=headers,
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["follow_up_status"] == "IN_PROGRESS"
