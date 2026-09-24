from __future__ import annotations

"""
API-level acceptance tests for the Election Addendum Relatedness-Review
Workflow API: authentication/authorization, the full happy-path state
machine over HTTP, item-level blocking rules, and cross-tenant isolation.
"""

import uuid
from datetime import date, datetime, timedelta, timezone

from app.core.security import create_access_token
from app.models.user import User
from tests.conftest import TEST_USER_ID
from tests.test_election_addendum_mandatory_workflow import (
    _make_admission,
    _make_benefit_period,
    _make_patient,
)
from app.billing.models.election_addendum_request import ElectionAddendumRequest


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
        full_name="Addendum Workflow API Test Actor",
        role=role,
        discipline=discipline,
        active=active,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _make_requirement(db_session, tenant_id):
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(
        db_session, patient, tenant_id, election_signed_at=datetime(2026, 10, 1, tzinfo=timezone.utc)
    )
    bp = _make_benefit_period(db_session, patient, tenant_id, election_date=date(2026, 10, 1))
    req = ElectionAddendumRequest(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient.id,
        admission_id=admission.id,
        benefit_period_id=bp.id,
        trigger_type="MANDATORY_INITIAL_ELECTION",
        election_effective_date=date(2026, 10, 1),
        required_by_at=datetime(2026, 10, 6, tzinfo=timezone.utc),
        mandatory_rule_applies=True,
        workflow_status="REQUIREMENT_CREATED",
        created_by=str(TEST_USER_ID),
    )
    db_session.add(req)
    db_session.commit()
    return patient, admission, req


def test_unauthenticated_start_review_is_rejected(client, db_session):
    tenant_id = uuid.UUID(str(db_session.info["tenant_id"]))
    _, _, req = _make_requirement(db_session, tenant_id)
    resp = client.post(
        f"/election-addendum-requests/{req.id}/relatedness-review",
        json={"reason": "unusual case"},
    )
    assert resp.status_code == 401


def test_unauthorized_role_is_rejected(client, db_session):
    """SCHEDULER is a valid platform role but has no addendum-workflow authority."""
    tenant_id_str = db_session.info["tenant_id"]
    tenant_id = uuid.UUID(str(tenant_id_str))
    _, _, req = _make_requirement(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id_str, role="SCHEDULER", discipline=None)
    headers = _headers("SCHEDULER", tenant_id_str, user_id=actor.id)

    resp = client.post(
        f"/election-addendum-requests/{req.id}/relatedness-review",
        json={"reason": "unusual case"},
        headers=headers,
    )
    assert resp.status_code == 403


def test_cross_tenant_get_returns_404(client, db_session):
    tenant_id_str = db_session.info["tenant_id"]
    tenant_id = uuid.UUID(str(tenant_id_str))
    _, _, req = _make_requirement(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id_str, role="RN", discipline="RN")

    other_tenant_headers = _headers("RN", uuid.uuid4(), user_id=actor.id)
    resp = client.get(f"/election-addendum-requests/{req.id}", headers=other_tenant_headers)
    assert resp.status_code == 404


def test_cross_tenant_mutation_returns_404(client, db_session):
    tenant_id_str = db_session.info["tenant_id"]
    tenant_id = uuid.UUID(str(tenant_id_str))
    _, _, req = _make_requirement(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id_str, role="RN", discipline="RN")

    other_tenant_headers = _headers("RN", uuid.uuid4(), user_id=actor.id)
    resp = client.post(
        f"/election-addendum-requests/{req.id}/relatedness-review",
        json={"reason": "unusual case"},
        headers=other_tenant_headers,
    )
    assert resp.status_code == 404


def test_full_happy_path_over_http(client, db_session):
    tenant_id_str = db_session.info["tenant_id"]
    tenant_id = uuid.UUID(str(tenant_id_str))
    _, _, req = _make_requirement(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id_str, role="RN", discipline="RN")
    headers = _headers("RN", tenant_id_str, user_id=actor.id)

    started = client.post(
        f"/election-addendum-requests/{req.id}/relatedness-review",
        json={"reason": "Dialysis and specialty medications require relatedness review"},
        headers=headers,
    )
    assert started.status_code == 200, started.text
    assert started.json()["workflow_status"] == "PENDING_RELATEDNESS_REVIEW"

    item_resp = client.post(
        f"/election-addendum-requests/{req.id}/relatedness-items",
        json={
            "determination_type": "DIALYSIS_TREATMENT",
            "description": "Ongoing hemodialysis",
            "effective_date": "2026-10-02",
            "current_provider_or_supplier": "Acme Dialysis Center",
        },
        headers=headers,
    )
    assert item_resp.status_code == 200, item_resp.text
    item_id = item_resp.json()["id"]
    assert item_resp.json()["relationship_status"] == "PENDING_REVIEW"

    listed = client.get(f"/election-addendum-requests/{req.id}/relatedness-items", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    determined = client.post(
        f"/election-addendum-requests/{req.id}/relatedness-items/{item_id}/determination",
        json={
            "relationship_status": "UNRELATED",
            "coverage_status": "NOT_COVERED",
            "coverage_owner": "NON_HOSPICE_MEDICARE",
            "clinical_rationale": "Dialysis for ESRD is not related to the terminal hospice diagnosis",
        },
        headers=headers,
    )
    assert determined.status_code == 200, determined.text
    assert determined.json()["relationship_status"] == "UNRELATED"

    completed_review = client.post(
        f"/election-addendum-requests/{req.id}/relatedness-review/complete",
        json={"clinical_rationale": "All disputed items reviewed and determined"},
        headers=headers,
    )
    assert completed_review.status_code == 200, completed_review.text
    assert completed_review.json()["workflow_status"] == "READY_FOR_GENERATION"

    generated = client.post(
        f"/election-addendum-requests/{req.id}/generate",
        json={"document_reference": "doc-ref-001", "document_version": 1},
        headers=headers,
    )
    assert generated.status_code == 200, generated.text
    assert generated.json()["workflow_status"] == "ADDENDUM_GENERATED"
    generated_at = generated.json()["generated_at"]

    furnished = client.post(
        f"/election-addendum-requests/{req.id}/furnish",
        json={
            "furnished_at": generated_at,
            "furnished_to": "PATIENT",
            "furnishing_method": "IN_PERSON",
            "bfcc_qio_information_furnished": True,
        },
        headers=headers,
    )
    assert furnished.status_code == 200, furnished.text
    assert furnished.json()["workflow_status"] == "ADDENDUM_FURNISHED"

    acknowledged = client.post(
        f"/election-addendum-requests/{req.id}/acknowledgment",
        json={"acknowledgment_status": "SIGNED_BY_PATIENT", "acknowledgment_document_reference": "doc-ref-001"},
        headers=headers,
    )
    assert acknowledged.status_code == 200, acknowledged.text
    assert acknowledged.json()["acknowledgment_status"] == "SIGNED_BY_PATIENT"

    audit = client.get(f"/election-addendum-requests/{req.id}/audit", headers=headers)
    assert audit.status_code == 200
    event_types = [e["event_type"] for e in audit.json()]
    assert event_types == [
        "RELATEDNESS_REVIEW_STARTED",
        "RELATEDNESS_ITEM_CREATED",
        "RELATEDNESS_ITEM_DETERMINED",
        "RELATEDNESS_DETERMINED",
        "ADDENDUM_GENERATED",
        "ADDENDUM_FURNISHED",
        "ACKNOWLEDGMENT_RECORDED",
    ]


def test_generation_blocked_before_review_complete_returns_422(client, db_session):
    tenant_id_str = db_session.info["tenant_id"]
    tenant_id = uuid.UUID(str(tenant_id_str))
    _, _, req = _make_requirement(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id_str, role="RN", discipline="RN")
    headers = _headers("RN", tenant_id_str, user_id=actor.id)

    resp = client.post(
        f"/election-addendum-requests/{req.id}/generate",
        json={"document_reference": "doc-ref", "document_version": 1},
        headers=headers,
    )
    assert resp.status_code == 422


def test_exception_from_open_state_over_http(client, db_session):
    tenant_id_str = db_session.info["tenant_id"]
    tenant_id = uuid.UUID(str(tenant_id_str))
    _, _, req = _make_requirement(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id_str, role="RN", discipline="RN")
    headers = _headers("RN", tenant_id_str, user_id=actor.id)

    resp = client.post(
        f"/election-addendum-requests/{req.id}/exception",
        json={
            "exception_type": "PATIENT_DIED",
            "exception_occurred_at": datetime.now(timezone.utc).isoformat(),
            "reason": "Patient expired before furnishing was possible",
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["workflow_status"] == "EXCEPTION_CLOSED"


def test_physician_review_request_over_http(client, db_session):
    tenant_id_str = db_session.info["tenant_id"]
    tenant_id = uuid.UUID(str(tenant_id_str))
    _, _, req = _make_requirement(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id_str, role="RN", discipline="RN")
    headers = _headers("RN", tenant_id_str, user_id=actor.id)

    started = client.post(
        f"/election-addendum-requests/{req.id}/relatedness-review",
        json={"reason": "Dialysis requires relatedness review"},
        headers=headers,
    )
    assert started.status_code == 200, started.text
    required_by_at_before = started.json()["required_by_at"]

    physician = _make_user(db_session, tenant_id_str, role="MD", discipline="MD")
    physician_id = str(physician.id)
    resp = client.post(
        f"/election-addendum-requests/{req.id}/physician-review",
        json={"physician_user_id": physician_id},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["physician_review_required"] is True
    assert body["physician_review_requested_at"] is not None
    assert body["physician_reviewer_user_id"] == physician_id
    # Physician-review-requested does not stop or advance the compliance
    # clock or the review-state machine.
    assert body["workflow_status"] == "PENDING_RELATEDNESS_REVIEW"
    assert body["required_by_at"] == required_by_at_before

    audit = client.get(f"/election-addendum-requests/{req.id}/audit", headers=headers)
    assert audit.status_code == 200
    events = audit.json()
    event_types = [e["event_type"] for e in events]
    assert "PHYSICIAN_REVIEW_REQUESTED" in event_types
    requested_event = next(e for e in events if e["event_type"] == "PHYSICIAN_REVIEW_REQUESTED")
    # Actor identity/discipline comes from the authenticated account, never
    # from the request payload (this schema doesn't even accept one).
    assert requested_event["actor_user_id"] == str(actor.id)
    assert requested_event["actor_account_discipline"] == "RN"
    assert requested_event["new_value"]["physician_reviewer_user_id"] == physician_id


def test_physician_review_request_cross_tenant_returns_404(client, db_session):
    tenant_id_str = db_session.info["tenant_id"]
    tenant_id = uuid.UUID(str(tenant_id_str))
    _, _, req = _make_requirement(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id_str, role="RN", discipline="RN")
    other_tenant_headers = _headers("RN", uuid.uuid4(), user_id=actor.id)

    resp = client.post(
        f"/election-addendum-requests/{req.id}/physician-review",
        json={"physician_user_id": str(uuid.uuid4())},
        headers=other_tenant_headers,
    )
    assert resp.status_code == 404


def test_physician_review_complete_over_http(client, db_session):
    tenant_id_str = db_session.info["tenant_id"]
    tenant_id = uuid.UUID(str(tenant_id_str))
    _, _, req = _make_requirement(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id_str, role="RN", discipline="RN")
    headers = _headers("RN", tenant_id_str, user_id=actor.id)

    client.post(
        f"/election-addendum-requests/{req.id}/relatedness-review",
        json={"reason": "Dialysis requires relatedness review"},
        headers=headers,
    )
    item_resp = client.post(
        f"/election-addendum-requests/{req.id}/relatedness-items",
        json={
            "determination_type": "DIALYSIS_TREATMENT",
            "description": "Ongoing hemodialysis",
            "effective_date": "2026-10-02",
        },
        headers=headers,
    )
    item_id = item_resp.json()["id"]
    physician = _make_user(db_session, tenant_id_str, role="MD", discipline="MD")
    physician_id = str(physician.id)
    client.post(
        f"/election-addendum-requests/{req.id}/physician-review",
        json={"physician_user_id": physician_id},
        headers=headers,
    )

    # Physician review cannot be completed while a required item
    # determination is still PENDING_REVIEW.
    blocked = client.post(
        f"/election-addendum-requests/{req.id}/physician-review/complete",
        json={"rationale": "premature"},
        headers=headers,
    )
    assert blocked.status_code == 422

    client.post(
        f"/election-addendum-requests/{req.id}/relatedness-items/{item_id}/determination",
        json={
            "relationship_status": "UNRELATED",
            "coverage_status": "NOT_COVERED",
            "coverage_owner": "NON_HOSPICE_MEDICARE",
            "clinical_rationale": "Dialysis for ESRD is not related to the terminal hospice diagnosis",
        },
        headers=headers,
    )

    completed = client.post(
        f"/election-addendum-requests/{req.id}/physician-review/complete",
        json={"rationale": "Physician confirms dialysis unrelated"},
        headers=headers,
    )
    assert completed.status_code == 200, completed.text
    body = completed.json()
    assert body["physician_reviewed_at"] is not None
    assert body["physician_review_rationale"] == "Physician confirms dialysis unrelated"
    # Physician review being complete now permits relatedness-review
    # completion (the next valid transition) -- the gate that was blocking
    # it is satisfied, not bypassed.
    review_complete = client.post(
        f"/election-addendum-requests/{req.id}/relatedness-review/complete",
        json={"clinical_rationale": "All disputed items reviewed and determined"},
        headers=headers,
    )
    assert review_complete.status_code == 200, review_complete.text
    assert review_complete.json()["workflow_status"] == "READY_FOR_GENERATION"

    audit = client.get(f"/election-addendum-requests/{req.id}/audit", headers=headers)
    events = audit.json()
    event_types = [e["event_type"] for e in events]
    assert "PHYSICIAN_REVIEW_COMPLETED" in event_types
    completed_event = next(e for e in events if e["event_type"] == "PHYSICIAN_REVIEW_COMPLETED")
    assert completed_event["actor_user_id"] == str(actor.id)
    assert completed_event["reason"] == "Physician confirms dialysis unrelated"


def test_physician_review_complete_cross_tenant_returns_404(client, db_session):
    tenant_id_str = db_session.info["tenant_id"]
    tenant_id = uuid.UUID(str(tenant_id_str))
    _, _, req = _make_requirement(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id_str, role="RN", discipline="RN")
    other_tenant_headers = _headers("RN", uuid.uuid4(), user_id=actor.id)

    resp = client.post(
        f"/election-addendum-requests/{req.id}/physician-review/complete",
        json={"rationale": "n/a"},
        headers=other_tenant_headers,
    )
    assert resp.status_code == 404


def test_update_workflow_over_http(client, db_session):
    tenant_id_str = db_session.info["tenant_id"]
    tenant_id = uuid.UUID(str(tenant_id_str))
    _, _, req = _make_requirement(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id_str, role="RN", discipline="RN")
    headers = _headers("RN", tenant_id_str, user_id=actor.id)

    # Drive the original (version 1) request all the way through furnishing.
    client.post(
        f"/election-addendum-requests/{req.id}/relatedness-review",
        json={"reason": "Dialysis requires relatedness review"},
        headers=headers,
    )
    item_resp = client.post(
        f"/election-addendum-requests/{req.id}/relatedness-items",
        json={
            "determination_type": "DIALYSIS_TREATMENT",
            "description": "Ongoing hemodialysis",
            "effective_date": "2026-10-02",
        },
        headers=headers,
    )
    item_id = item_resp.json()["id"]
    client.post(
        f"/election-addendum-requests/{req.id}/relatedness-items/{item_id}/determination",
        json={
            "relationship_status": "UNRELATED",
            "coverage_status": "NOT_COVERED",
            "coverage_owner": "NON_HOSPICE_MEDICARE",
            "clinical_rationale": "Not related to the terminal hospice diagnosis",
        },
        headers=headers,
    )
    client.post(
        f"/election-addendum-requests/{req.id}/relatedness-review/complete",
        json={"clinical_rationale": "All disputed items reviewed and determined"},
        headers=headers,
    )
    generated = client.post(
        f"/election-addendum-requests/{req.id}/generate",
        json={"document_reference": "doc-ref-001", "document_version": 1},
        headers=headers,
    )
    generated_at = generated.json()["generated_at"]
    furnished = client.post(
        f"/election-addendum-requests/{req.id}/furnish",
        json={
            "furnished_at": generated_at,
            "furnished_to": "PATIENT",
            "furnishing_method": "IN_PERSON",
            "bfcc_qio_information_furnished": True,
        },
        headers=headers,
    )
    assert furnished.status_code == 200, furnished.text
    original = furnished.json()
    assert original["workflow_status"] == "ADDENDUM_FURNISHED"

    original_id = original["id"]
    original_version = original["version_number"]
    original_document_reference = original["document_reference"]
    original_document_version = original["document_version"]
    original_furnished_at = original["furnished_at"]
    original_items_before = client.get(
        f"/election-addendum-requests/{original_id}/relatedness-items", headers=headers
    ).json()

    # --- Negative/contract checks before the happy-path mutation ---
    unauthenticated = client.post(f"/election-addendum-requests/{original_id}/updates", json={"poc_change_date": "2026-10-10"})
    assert unauthenticated.status_code == 401

    unauthorized_actor = _make_user(db_session, tenant_id_str, role="SCHEDULER", discipline=None)
    unauthorized_headers = _headers("SCHEDULER", tenant_id_str, user_id=unauthorized_actor.id)
    unauthorized = client.post(
        f"/election-addendum-requests/{original_id}/updates",
        json={"poc_change_date": "2026-10-10"},
        headers=unauthorized_headers,
    )
    assert unauthorized.status_code == 403

    other_tenant_actor = _make_user(db_session, tenant_id_str, role="RN", discipline="RN")
    other_tenant_headers = _headers("RN", uuid.uuid4(), user_id=other_tenant_actor.id)
    cross_tenant = client.post(
        f"/election-addendum-requests/{original_id}/updates",
        json={"poc_change_date": "2026-10-10"},
        headers=other_tenant_headers,
    )
    assert cross_tenant.status_code == 404

    malformed = client.post(
        f"/election-addendum-requests/{original_id}/updates",
        json={"poc_change_date": "not-a-date"},
        headers=headers,
    )
    assert malformed.status_code == 422

    # Invalid source state: an addendum request whose election predates the
    # mandatory rule's effective date can never generate a valid update
    # requirement -- the service raises ElectionAddendumComplianceError,
    # which the router maps to 422 (not a fabricated 409).
    from datetime import date as _date

    pre_rule_patient, pre_rule_admission, pre_rule_req = _make_requirement(db_session, tenant_id)
    pre_rule_req.election_effective_date = _date(2025, 1, 1)
    db_session.commit()
    invalid_state = client.post(
        f"/election-addendum-requests/{pre_rule_req.id}/updates",
        json={"poc_change_date": "2025-01-10"},
        headers=headers,
    )
    assert invalid_state.status_code == 422

    # --- Happy path ---
    update_resp = client.post(
        f"/election-addendum-requests/{original_id}/updates",
        json={"poc_change_date": "2026-10-10"},
        headers=headers,
    )
    assert update_resp.status_code == 200, update_resp.text
    new_row = update_resp.json()

    assert new_row["id"] != original_id
    assert new_row["version_number"] == original_version + 1
    assert new_row["supersedes_request_id"] == original_id
    assert new_row["trigger_type"] == "PLAN_OF_CARE_CHANGE"
    # Three-day PLAN_OF_CARE_CHANGE furnishing deadline from the trigger date.
    assert new_row["required_by_at"] == "2026-10-13T00:00:00+00:00"
    # New version starts a fresh review cycle, not falsely furnished.
    assert new_row["workflow_status"] == "REQUIREMENT_CREATED"
    assert new_row["furnished_at"] is None
    assert new_row["document_reference"] is None

    # Re-fetch the original (now-superseded) request and confirm it is
    # untouched: same ID, same version, same document/furnishing evidence,
    # same relatedness history.
    refetched_original = client.get(f"/election-addendum-requests/{original_id}", headers=headers)
    assert refetched_original.status_code == 200
    refetched_body = refetched_original.json()
    assert refetched_body["id"] == original_id
    assert refetched_body["version_number"] == original_version
    assert refetched_body["document_reference"] == original_document_reference
    assert refetched_body["document_version"] == original_document_version
    assert refetched_body["furnished_at"] == original_furnished_at
    assert refetched_body["workflow_status"] == "ADDENDUM_FURNISHED"

    original_items_after = client.get(
        f"/election-addendum-requests/{original_id}/relatedness-items", headers=headers
    ).json()
    assert original_items_after == original_items_before

    # Audit: new version has ADDENDUM_UPDATE_REQUIRED, prior version has
    # ADDENDUM_SUPERSEDED, both correctly linked back to each other.
    new_audit = client.get(f"/election-addendum-requests/{new_row['id']}/audit", headers=headers).json()
    new_event_types = [e["event_type"] for e in new_audit]
    assert "ADDENDUM_UPDATE_REQUIRED" in new_event_types
    update_event = next(e for e in new_audit if e["event_type"] == "ADDENDUM_UPDATE_REQUIRED")
    assert update_event["new_value"]["supersedes_request_id"] == original_id
    assert update_event["actor_user_id"] == str(actor.id)

    original_audit = client.get(f"/election-addendum-requests/{original_id}/audit", headers=headers).json()
    original_event_types = [e["event_type"] for e in original_audit]
    assert "ADDENDUM_SUPERSEDED" in original_event_types
    superseded_event = next(e for e in original_audit if e["event_type"] == "ADDENDUM_SUPERSEDED")
    assert superseded_event["new_value"]["superseded_by_id"] == new_row["id"]


def test_updated_addendum_version_completes_own_review_generation_and_furnishing(client, db_session):
    """Layer 2 of the CMS three-day update obligation: creating a
    version-2 row (ADDENDUM_UPDATE_REQUIRED) only opens the update
    requirement. This proves the version-2 row can independently complete
    its own relatedness review, be generated, be furnished, and retain
    its own furnishing/audit evidence -- while version-1's evidence stays
    untouched throughout."""
    tenant_id_str = db_session.info["tenant_id"]
    tenant_id = uuid.UUID(str(tenant_id_str))
    _, _, req = _make_requirement(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id_str, role="RN", discipline="RN")
    headers = _headers("RN", tenant_id_str, user_id=actor.id)

    # Drive version 1 through to furnishing.
    client.post(
        f"/election-addendum-requests/{req.id}/relatedness-review",
        json={"reason": "Dialysis requires relatedness review"},
        headers=headers,
    )
    v1_item_resp = client.post(
        f"/election-addendum-requests/{req.id}/relatedness-items",
        json={
            "determination_type": "DIALYSIS_TREATMENT",
            "description": "Ongoing hemodialysis",
            "effective_date": "2026-10-02",
        },
        headers=headers,
    )
    v1_item_id = v1_item_resp.json()["id"]
    client.post(
        f"/election-addendum-requests/{req.id}/relatedness-items/{v1_item_id}/determination",
        json={
            "relationship_status": "UNRELATED",
            "coverage_status": "NOT_COVERED",
            "coverage_owner": "NON_HOSPICE_MEDICARE",
            "clinical_rationale": "Not related to the terminal hospice diagnosis",
        },
        headers=headers,
    )
    client.post(
        f"/election-addendum-requests/{req.id}/relatedness-review/complete",
        json={"clinical_rationale": "All disputed items reviewed and determined"},
        headers=headers,
    )
    v1_generated = client.post(
        f"/election-addendum-requests/{req.id}/generate",
        json={"document_reference": "doc-ref-v1", "document_version": 1},
        headers=headers,
    )
    v1_generated_at = v1_generated.json()["generated_at"]
    v1_furnished = client.post(
        f"/election-addendum-requests/{req.id}/furnish",
        json={
            "furnished_at": v1_generated_at,
            "furnished_to": "PATIENT",
            "furnishing_method": "IN_PERSON",
            "bfcc_qio_information_furnished": True,
        },
        headers=headers,
    )
    assert v1_furnished.status_code == 200, v1_furnished.text
    v1 = v1_furnished.json()
    v1_id = v1["id"]
    v1_document_reference = v1["document_reference"]
    v1_furnished_at = v1["furnished_at"]

    # A qualifying POC change opens the update requirement (Layer 1,
    # already proven by test_update_workflow_over_http). Continue past it
    # into Layer 2.
    update_resp = client.post(
        f"/election-addendum-requests/{v1_id}/updates",
        json={"poc_change_date": "2026-10-10"},
        headers=headers,
    )
    assert update_resp.status_code == 200, update_resp.text
    v2 = update_resp.json()
    v2_id = v2["id"]
    assert v2["workflow_status"] == "REQUIREMENT_CREATED"

    # --- Version-2 completes its own relatedness review ---
    v2_started = client.post(
        f"/election-addendum-requests/{v2_id}/relatedness-review",
        json={"reason": "Plan-of-care change altered the dialysis determination"},
        headers=headers,
    )
    assert v2_started.status_code == 200, v2_started.text
    assert v2_started.json()["workflow_status"] == "PENDING_RELATEDNESS_REVIEW"

    v2_item_resp = client.post(
        f"/election-addendum-requests/{v2_id}/relatedness-items",
        json={
            "determination_type": "DIALYSIS_TREATMENT",
            "description": "Hemodialysis frequency changed under new plan of care",
            "effective_date": "2026-10-10",
        },
        headers=headers,
    )
    assert v2_item_resp.status_code == 200, v2_item_resp.text
    v2_item_id = v2_item_resp.json()["id"]

    v2_determined = client.post(
        f"/election-addendum-requests/{v2_id}/relatedness-items/{v2_item_id}/determination",
        json={
            "relationship_status": "UNRELATED",
            "coverage_status": "NOT_COVERED",
            "coverage_owner": "NON_HOSPICE_MEDICARE",
            "clinical_rationale": "Increased dialysis frequency remains unrelated to the terminal hospice diagnosis",
        },
        headers=headers,
    )
    assert v2_determined.status_code == 200, v2_determined.text

    # The changed dialysis frequency is an unusual case warranting
    # physician review before the updated determination is finalized --
    # exercises the same physician-review gate proven for version 1,
    # against version 2's own row.
    v2_physician = _make_user(db_session, tenant_id_str, role="MD", discipline="MD")
    v2_review_requested = client.post(
        f"/election-addendum-requests/{v2_id}/physician-review",
        json={"physician_user_id": str(v2_physician.id)},
        headers=headers,
    )
    assert v2_review_requested.status_code == 200, v2_review_requested.text
    assert v2_review_requested.json()["physician_reviewer_user_id"] == str(v2_physician.id)

    v2_review_completed_by_physician = client.post(
        f"/election-addendum-requests/{v2_id}/physician-review/complete",
        json={"rationale": "Physician confirms increased dialysis frequency remains unrelated"},
        headers=headers,
    )
    assert v2_review_completed_by_physician.status_code == 200, v2_review_completed_by_physician.text
    assert v2_review_completed_by_physician.json()["physician_reviewed_at"] is not None

    v2_review_complete = client.post(
        f"/election-addendum-requests/{v2_id}/relatedness-review/complete",
        json={"clinical_rationale": "Updated determination reviewed and confirmed"},
        headers=headers,
    )
    assert v2_review_complete.status_code == 200, v2_review_complete.text
    assert v2_review_complete.json()["workflow_status"] == "READY_FOR_GENERATION"
    # Version-2's own determination/rationale never overwrites version-1's.
    v1_items_still = client.get(f"/election-addendum-requests/{v1_id}/relatedness-items", headers=headers).json()
    assert len(v1_items_still) == 1
    assert v1_items_still[0]["id"] == v1_item_id
    assert v1_items_still[0]["clinical_rationale"] == "Not related to the terminal hospice diagnosis"

    # --- Version-2 is independently generated ---
    v2_generated = client.post(
        f"/election-addendum-requests/{v2_id}/generate",
        json={"document_reference": "doc-ref-v2", "document_version": 1},
        headers=headers,
    )
    assert v2_generated.status_code == 200, v2_generated.text
    v2_generated_body = v2_generated.json()
    assert v2_generated_body["workflow_status"] == "ADDENDUM_GENERATED"
    assert v2_generated_body["document_reference"] == "doc-ref-v2"
    v2_generated_at = v2_generated_body["generated_at"]

    # Furnishing must occur strictly after generation (generation !=
    # furnishing) and, in the happy path, on or before required_by_at.
    v2_furnished_at_dt = datetime.fromisoformat(v2_generated_at) + timedelta(hours=1)
    v2_furnished_at_iso = v2_furnished_at_dt.isoformat()

    # --- Version-2 is independently furnished within its own 3-day clock ---
    v2_furnished = client.post(
        f"/election-addendum-requests/{v2_id}/furnish",
        json={
            "furnished_at": v2_furnished_at_iso,
            "furnished_to": "PATIENT",
            "furnishing_method": "IN_PERSON",
            "bfcc_qio_information_furnished": True,
        },
        headers=headers,
    )
    assert v2_furnished.status_code == 200, v2_furnished.text
    v2_final = v2_furnished.json()
    assert v2_final["workflow_status"] == "ADDENDUM_FURNISHED"
    assert v2_final["document_reference"] == "doc-ref-v2"
    assert v2_final["furnished_at"] == v2_furnished_at_iso
    assert v2_final["furnished_at"] != v2_final["generated_at"]
    # The version-2 furnishing deadline is the 3-day PLAN_OF_CARE_CHANGE
    # clock computed at update-creation time, not the original 5-day
    # initial-election clock.
    assert v2_final["required_by_at"] == "2026-10-13T00:00:00+00:00"
    required_by_dt = datetime.fromisoformat(v2_final["required_by_at"])
    assert v2_furnished_at_dt <= required_by_dt, "happy-path furnishing must land on or before required_by_at"
    assert v2_furnished_at_dt > datetime.fromisoformat(v2_final["generated_at"])

    # --- Version-2's own audit trail is retrievable and complete ---
    v2_audit = client.get(f"/election-addendum-requests/{v2_id}/audit", headers=headers)
    assert v2_audit.status_code == 200
    v2_event_types = [e["event_type"] for e in v2_audit.json()]
    assert v2_event_types == [
        "ADDENDUM_UPDATE_REQUIRED",
        "RELATEDNESS_REVIEW_STARTED",
        "RELATEDNESS_ITEM_CREATED",
        "RELATEDNESS_ITEM_DETERMINED",
        "PHYSICIAN_REVIEW_REQUESTED",
        "PHYSICIAN_REVIEW_COMPLETED",
        "RELATEDNESS_DETERMINED",
        "ADDENDUM_GENERATED",
        "ADDENDUM_FURNISHED",
    ]
    # The /audit route itself scopes to this addendum_request_id (it
    # filters ElectionAddendumAuditEvent.addendum_request_id == req.id),
    # so every returned row is already proven to belong to version 2.
    generated_event = next(e for e in v2_audit.json() if e["event_type"] == "ADDENDUM_GENERATED")
    assert generated_event["actor_user_id"] == str(actor.id)
    furnished_event = next(e for e in v2_audit.json() if e["event_type"] == "ADDENDUM_FURNISHED")
    assert furnished_event["actor_user_id"] == str(actor.id)
    assert furnished_event["new_value"]["furnished_to"] == "PATIENT"

    # --- Version-1's evidence remains completely untouched throughout ---
    v1_refetched = client.get(f"/election-addendum-requests/{v1_id}", headers=headers).json()
    assert v1_refetched["workflow_status"] == "ADDENDUM_FURNISHED"
    assert v1_refetched["document_reference"] == v1_document_reference
    assert v1_refetched["furnished_at"] == v1_furnished_at

    v1_audit = client.get(f"/election-addendum-requests/{v1_id}/audit", headers=headers)
    v1_event_types = [e["event_type"] for e in v1_audit.json()]
    # Version-1's own trail ends with its furnishing plus the
    # ADDENDUM_SUPERSEDED notice from the update -- never any version-2
    # event bleeding into version-1's audit history.
    assert v1_event_types == [
        "RELATEDNESS_REVIEW_STARTED",
        "RELATEDNESS_ITEM_CREATED",
        "RELATEDNESS_ITEM_DETERMINED",
        "RELATEDNESS_DETERMINED",
        "ADDENDUM_GENERATED",
        "ADDENDUM_FURNISHED",
        "ADDENDUM_SUPERSEDED",
    ]


def test_payload_discipline_is_ignored_actor_discipline_used(client, db_session):
    """Discipline must come from the authenticated actor's account, never
    from a request payload -- this API's schemas don't even accept a
    discipline field, but verify the audit trail records the actor's real
    account discipline regardless."""
    tenant_id_str = db_session.info["tenant_id"]
    tenant_id = uuid.UUID(str(tenant_id_str))
    _, _, req = _make_requirement(db_session, tenant_id)
    actor = _make_user(db_session, tenant_id_str, role="SW", discipline="SW")
    headers = _headers("SW", tenant_id_str, user_id=actor.id)

    client.post(
        f"/election-addendum-requests/{req.id}/relatedness-review",
        json={"reason": "unusual case"},
        headers=headers,
    )
    audit = client.get(f"/election-addendum-requests/{req.id}/audit", headers=headers)
    events = audit.json()
    assert events[0]["actor_account_discipline"] == "SW"
    assert events[0]["actor_user_id"] == str(actor.id)
