from __future__ import annotations

"""
API-level acceptance tests for the Election Compliance-Review API
(issue #142/#145 API phase): retrieval, resolution (including atomic
mandatory-addendum-requirement creation), and reopen via HTTP.
"""

import uuid
from datetime import date, datetime, timezone

import pytest

from app.core.security import create_access_token
from app.models.user import User
from tests.conftest import TEST_USER_ID
from tests.test_election_addendum_mandatory_workflow import (
    _make_admission,
    _make_benefit_period,
    _make_patient,
)
from app.billing.services import election_addendum_service as svc


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
        full_name="Compliance API Test Actor",
        role=role,
        discipline=discipline,
        active=active,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _make_open_review(db_session, tenant_id):
    """Opens a compliance review with no benefit_period yet (missing
    election date), then creates a valid benefit_period afterward for use
    in the resolve() call -- mirrors tests/test_election_compliance_review.py."""
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(
        db_session, patient, tenant_id, election_signed_at=datetime(2026, 10, 1, tzinfo=timezone.utc)
    )
    outcome = svc.get_or_create_mandatory_initial_addendum_requirement(
        db_session, tenant_id=tenant_id, admission_id=admission.id, created_by_user_id=TEST_USER_ID
    )
    assert outcome.outcome == "COMPLIANCE_REVIEW_REQUIRED"
    bp = _make_benefit_period(db_session, patient, tenant_id, election_date=date(2026, 10, 1))
    return patient, admission, bp, outcome.compliance_obligation


def test_unauthenticated_resolve_is_rejected(client, db_session):
    tenant_id = uuid.UUID(str(db_session.info["tenant_id"]))
    _, _, bp, obligation = _make_open_review(db_session, tenant_id)
    resp = client.post(
        f"/election-compliance-reviews/{obligation.id}/resolve",
        json={
            "benefit_period_id": str(bp.id),
            "resolved_election_date": "2026-10-01",
            "resolution_reason": "chart correction",
        },
    )
    assert resp.status_code == 401


def test_unauthorized_role_is_rejected(client, db_session):
    """SCHEDULER is a valid platform role but has no compliance-review authority."""
    tenant_id_str = db_session.info["tenant_id"]
    tenant_id = uuid.UUID(str(tenant_id_str))
    _, _, bp, obligation = _make_open_review(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id_str, role="SCHEDULER", discipline=None)
    headers = _headers("SCHEDULER", tenant_id_str, user_id=actor.id)

    resp = client.post(
        f"/election-compliance-reviews/{obligation.id}/resolve",
        json={
            "benefit_period_id": str(bp.id),
            "resolved_election_date": "2026-10-01",
            "resolution_reason": "chart correction",
        },
        headers=headers,
    )
    assert resp.status_code == 403


def test_get_and_list_compliance_reviews(client, db_session):
    tenant_id_str = db_session.info["tenant_id"]
    tenant_id = uuid.UUID(str(tenant_id_str))
    patient, admission, bp, obligation = _make_open_review(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id_str, role="RN", discipline="RN")
    headers = _headers("RN", tenant_id_str, user_id=actor.id)

    got = client.get(f"/election-compliance-reviews/{obligation.id}", headers=headers)
    assert got.status_code == 200
    assert got.json()["status"] == "OPEN"

    listed = client.get(f"/admissions/{admission.id}/election-compliance-reviews", headers=headers)
    assert listed.status_code == 200
    assert any(r["id"] == str(obligation.id) for r in listed.json())


def test_resolve_compliance_review_creates_mandatory_requirement(client, db_session):
    tenant_id_str = db_session.info["tenant_id"]
    tenant_id = uuid.UUID(str(tenant_id_str))
    patient, admission, bp, obligation = _make_open_review(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id_str, role="RN", discipline="RN")
    headers = _headers("RN", tenant_id_str, user_id=actor.id)

    resp = client.post(
        f"/election-compliance-reviews/{obligation.id}/resolve",
        json={
            "benefit_period_id": str(bp.id),
            "resolved_election_date": "2026-10-01",
            "resolution_reason": "chart correction confirmed with intake",
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "COMPLETED"
    assert body["mandatory_addendum_outcome"] in ("CREATED", "EXISTING")
    assert body["election_addendum_request_id"] is not None


def test_resolve_requires_reason(client, db_session):
    tenant_id_str = db_session.info["tenant_id"]
    tenant_id = uuid.UUID(str(tenant_id_str))
    patient, admission, bp, obligation = _make_open_review(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id_str, role="RN", discipline="RN")
    headers = _headers("RN", tenant_id_str, user_id=actor.id)

    resp = client.post(
        f"/election-compliance-reviews/{obligation.id}/resolve",
        json={
            "benefit_period_id": str(bp.id),
            "resolved_election_date": "2026-10-01",
            "resolution_reason": "",
        },
        headers=headers,
    )
    assert resp.status_code == 422


def test_resolve_rejects_cross_tenant_benefit_period(client, db_session):
    tenant_id_str = db_session.info["tenant_id"]
    tenant_id = uuid.UUID(str(tenant_id_str))
    patient, admission, bp, obligation = _make_open_review(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id_str, role="RN", discipline="RN")
    headers = _headers("RN", tenant_id_str, user_id=actor.id)

    # A benefit_period belonging to a *different* patient (simulates the
    # cross-patient/cross-tenant rejection path in the service layer).
    other_patient = _make_patient(db_session, tenant_id)
    other_bp = _make_benefit_period(db_session, other_patient, tenant_id, election_date=date(2026, 10, 1))

    resp = client.post(
        f"/election-compliance-reviews/{obligation.id}/resolve",
        json={
            "benefit_period_id": str(other_bp.id),
            "resolved_election_date": "2026-10-01",
            "resolution_reason": "chart correction",
        },
        headers=headers,
    )
    assert resp.status_code == 422


def test_reopen_resolved_review_requires_reason_and_preserves_resolution(client, db_session):
    tenant_id_str = db_session.info["tenant_id"]
    tenant_id = uuid.UUID(str(tenant_id_str))
    patient, admission, bp, obligation = _make_open_review(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id_str, role="RN", discipline="RN")
    headers = _headers("RN", tenant_id_str, user_id=actor.id)

    client.post(
        f"/election-compliance-reviews/{obligation.id}/resolve",
        json={
            "benefit_period_id": str(bp.id),
            "resolved_election_date": "2026-10-01",
            "resolution_reason": "chart correction confirmed with intake",
        },
        headers=headers,
    )

    missing_reason = client.post(
        f"/election-compliance-reviews/{obligation.id}/reopen", json={"reopen_reason": ""}, headers=headers
    )
    assert missing_reason.status_code == 409

    ok = client.post(
        f"/election-compliance-reviews/{obligation.id}/reopen",
        json={"reopen_reason": "New information received"},
        headers=headers,
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["status"] == "OPEN"

    audit = client.get(f"/election-compliance-reviews/{obligation.id}/audit", headers=headers)
    assert audit.status_code == 200
    event_types = [row["event_type"] for row in audit.json()]
    assert "RECORD_FINALIZED" in event_types
    assert "RECORD_REOPENED" in event_types


def test_cross_tenant_review_access_is_rejected(client, db_session):
    tenant_id_str = db_session.info["tenant_id"]
    tenant_id = uuid.UUID(str(tenant_id_str))
    patient, admission, bp, obligation = _make_open_review(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id_str, role="RN", discipline="RN")

    other_tenant_headers = _headers("RN", uuid.uuid4(), user_id=actor.id)
    resp = client.get(f"/election-compliance-reviews/{obligation.id}", headers=other_tenant_headers)
    assert resp.status_code == 404
