from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.core.security import create_access_token
from app.models.patient import Patient
from app.models.user import User
from tests.conftest import TEST_USER_ID, _test_tenant_id


def _make_patient(db_session, tenant_id):
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"BSAMEND-{uuid.uuid4().hex[:12]}",
        date_of_birth=date(1945, 6, 15),
        primary_diagnosis="Hospice qualifying diagnosis",
        status="ACTIVE",
        admission_status="PRE_REFERRAL",
        created_by=None,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _supervisor_headers(db_session, role="DPCS"):
    """A distinct user (not TEST_USER_ID) so self-approval tests are
    meaningful. Mirrors tests/test_rnica_amendments.py's helper of the
    same name/purpose.
    """
    tenant_id = uuid.UUID(_test_tenant_id())
    user_id = uuid.uuid4()
    user = db_session.query(User).filter(User.id == user_id).first()
    if user is None:
        db_session.add(
            User(
                id=user_id,
                tenant_id=tenant_id,
                email=f"{role.lower()}.{user_id.hex[:8]}@example.com",
                full_name=f"Test {role.title()}",
                role=role,
                active=True,
            )
        )
        db_session.commit()

    token = create_access_token(
        user_id=user_id,
        role=role,
        tenant_id=tenant_id,
        email=f"{role.lower()}@example.com",
    )
    return {"Authorization": f"Bearer {token}"}, user_id


@pytest.mark.integration
def test_submit_validates_category_reason_source_and_blank_text(client, db_session, rn_headers, tenant):
    patient = _make_patient(db_session, uuid.UUID(tenant.id))
    client.get(f"/visits/body-systems/patients/{patient.id}/respiratory", headers=rn_headers)

    bad_category = client.post(
        f"/visits/body-systems/patients/{patient.id}/respiratory/correction-request",
        json={
            "amendmentCategory": "NOT_A_CATEGORY",
            "reasonCode": "OMITTED_FINDING",
            "requestedChange": "Something.",
        },
        headers=rn_headers,
    )
    assert bad_category.status_code == 400, bad_category.text

    bad_reason = client.post(
        f"/visits/body-systems/patients/{patient.id}/respiratory/correction-request",
        json={
            "amendmentCategory": "CLINICAL_CORRECTION",
            "reasonCode": "NOT_A_REASON",
            "requestedChange": "Something.",
        },
        headers=rn_headers,
    )
    assert bad_reason.status_code == 400, bad_reason.text

    bad_source = client.post(
        f"/visits/body-systems/patients/{patient.id}/respiratory/correction-request",
        json={
            "amendmentCategory": "CLINICAL_CORRECTION",
            "reasonCode": "OMITTED_FINDING",
            "requestedChange": "Something.",
            "requestSource": "NOT_A_SOURCE",
        },
        headers=rn_headers,
    )
    assert bad_source.status_code == 400, bad_source.text

    blank_text = client.post(
        f"/visits/body-systems/patients/{patient.id}/respiratory/correction-request",
        json={
            "amendmentCategory": "CLINICAL_CORRECTION",
            "reasonCode": "OMITTED_FINDING",
            "requestedChange": "   ",
        },
        headers=rn_headers,
    )
    assert blank_text.status_code == 400, blank_text.text

    default_source_resp = client.post(
        f"/visits/body-systems/patients/{patient.id}/respiratory/correction-request",
        json={
            "amendmentCategory": "CLINICAL_CORRECTION",
            "reasonCode": "OMITTED_FINDING",
            "requestedChange": "Something without an explicit requestSource.",
        },
        headers=rn_headers,
    )
    assert default_source_resp.status_code == 201, default_source_resp.text
    assert default_source_resp.json()["requestSource"] == "STAFF"


@pytest.mark.integration
def test_full_amendment_workflow_approve_never_mutates_original(client, db_session, rn_headers, tenant):
    patient = _make_patient(db_session, uuid.UUID(tenant.id))
    get_resp = client.get(f"/visits/body-systems/patients/{patient.id}/respiratory", headers=rn_headers)
    original_data = dict(get_resp.json()["data"])

    # Save some original content to confirm it is never overwritten by the
    # amendment workflow (only recorded as original_value_snapshot).
    client.put(
        f"/visits/body-systems/patients/{patient.id}/respiratory",
        headers=rn_headers,
        json={"data": {"oxygen_saturation": "94%"}, "reviewState": "in_progress"},
    )

    supervisor_headers, supervisor_id = _supervisor_headers(db_session, role="DPCS")

    create_resp = client.post(
        f"/visits/body-systems/patients/{patient.id}/respiratory/correction-request",
        json={
            "fieldReference": "data.oxygen_saturation",
            "amendmentCategory": "CLINICAL_CORRECTION",
            "reasonCode": "INCORRECT_VALUE",
            "requestedChange": "Oxygen saturation was documented incorrectly; should be 91%.",
            "originalValueSnapshot": "94%",
            "proposedValue": "91%",
        },
        headers=rn_headers,
    )
    assert create_resp.status_code == 201, create_resp.text
    created = create_resp.json()
    assert created["status"] == "PENDING"
    assert created["system"] == "respiratory"
    assert created["originalValueSnapshot"] == "94%"
    assert created["proposedValue"] == "91%"
    amendment_id = created["id"]

    list_resp = client.get(
        f"/visits/body-systems/patients/{patient.id}/respiratory/amendments", headers=rn_headers
    )
    assert list_resp.status_code == 200, list_resp.text
    assert any(a["id"] == amendment_id for a in list_resp.json()["amendments"])

    # Non-approval role cannot decide.
    forbidden_resp = client.post(
        f"/visits/body-systems/patients/{patient.id}/respiratory/amendments/{amendment_id}/approve",
        json={},
        headers=rn_headers,
    )
    assert forbidden_resp.status_code == 403, forbidden_resp.text

    approve_resp = client.post(
        f"/visits/body-systems/patients/{patient.id}/respiratory/amendments/{amendment_id}/approve",
        json={},
        headers=supervisor_headers,
    )
    assert approve_resp.status_code == 200, approve_resp.text
    approved = approve_resp.json()
    assert approved["status"] == "APPROVED"
    assert approved["decisionUserId"] == str(supervisor_id)
    assert approved["decisionTimestamp"] is not None

    # The original SystemAssessment content is never mutated by approval.
    reread_resp = client.get(f"/visits/body-systems/patients/{patient.id}/respiratory", headers=rn_headers)
    assert reread_resp.json()["data"] == {"oxygen_saturation": "94%"}

    # Cannot re-decide an already-decided amendment.
    redecide_resp = client.post(
        f"/visits/body-systems/patients/{patient.id}/respiratory/amendments/{amendment_id}/approve",
        json={},
        headers=supervisor_headers,
    )
    assert redecide_resp.status_code == 400, redecide_resp.text


@pytest.mark.integration
def test_deny_requires_reason(client, db_session, rn_headers, tenant):
    patient = _make_patient(db_session, uuid.UUID(tenant.id))
    client.get(f"/visits/body-systems/patients/{patient.id}/respiratory", headers=rn_headers)

    create_resp = client.post(
        f"/visits/body-systems/patients/{patient.id}/respiratory/correction-request",
        json={
            "amendmentCategory": "DOCUMENTATION_ERROR",
            "reasonCode": "INCORRECT_VALUE",
            "requestedChange": "Correct a documentation error.",
        },
        headers=rn_headers,
    )
    assert create_resp.status_code == 201, create_resp.text
    amendment_id = create_resp.json()["id"]

    supervisor_headers, supervisor_id = _supervisor_headers(db_session, role="SUPERVISOR")

    missing_reason_resp = client.post(
        f"/visits/body-systems/patients/{patient.id}/respiratory/amendments/{amendment_id}/deny",
        json={"decisionReason": "   "},
        headers=supervisor_headers,
    )
    assert missing_reason_resp.status_code == 422, missing_reason_resp.text

    deny_resp = client.post(
        f"/visits/body-systems/patients/{patient.id}/respiratory/amendments/{amendment_id}/deny",
        json={"decisionReason": "Not supported by documentation."},
        headers=supervisor_headers,
    )
    assert deny_resp.status_code == 200, deny_resp.text
    denied = deny_resp.json()
    assert denied["status"] == "DENIED"
    assert denied["decisionUserId"] == str(supervisor_id)
    assert denied["decisionReason"] == "Not supported by documentation."


@pytest.mark.integration
def test_submitter_cannot_approve_or_deny_own_amendment(client, db_session, tenant):
    patient = _make_patient(db_session, uuid.UUID(tenant.id))

    dpcs_headers, _dpcs_id = _supervisor_headers(db_session, role="DPCS")
    client.get(f"/visits/body-systems/patients/{patient.id}/respiratory", headers=dpcs_headers)

    create_resp = client.post(
        f"/visits/body-systems/patients/{patient.id}/respiratory/correction-request",
        json={
            "amendmentCategory": "CLARIFICATION",
            "reasonCode": "CLARIFICATION_NEEDED",
            "requestedChange": "Clarify documented finding.",
        },
        headers=dpcs_headers,
    )
    assert create_resp.status_code == 201, create_resp.text
    amendment_id = create_resp.json()["id"]

    self_approve_resp = client.post(
        f"/visits/body-systems/patients/{patient.id}/respiratory/amendments/{amendment_id}/approve",
        json={},
        headers=dpcs_headers,
    )
    assert self_approve_resp.status_code == 400, self_approve_resp.text

    self_deny_resp = client.post(
        f"/visits/body-systems/patients/{patient.id}/respiratory/amendments/{amendment_id}/deny",
        json={"decisionReason": "Self review not permitted."},
        headers=dpcs_headers,
    )
    assert self_deny_resp.status_code == 400, self_deny_resp.text


@pytest.mark.integration
def test_direct_edit_rejected_once_assessment_leaves_draft(client, db_session, rn_headers, tenant):
    """Documents the draft-vs-authenticated boundary enforced in
    save_respiratory_draft: once BodySystemsAssessment.status leaves
    "draft", direct field overwrite is rejected in favor of the amendment
    workflow above.
    """
    from app.models.body_systems import BodySystemsAssessment

    patient = _make_patient(db_session, uuid.UUID(tenant.id))
    get_resp = client.get(f"/visits/body-systems/patients/{patient.id}/respiratory", headers=rn_headers)
    assessment_id = uuid.UUID(get_resp.json()["bodySystemsAssessmentId"])

    assessment = db_session.query(BodySystemsAssessment).filter(BodySystemsAssessment.id == assessment_id).first()
    assessment.status = "recorded"
    db_session.add(assessment)
    db_session.commit()

    response = client.put(
        f"/visits/body-systems/patients/{patient.id}/respiratory",
        headers=rn_headers,
        json={"data": {"oxygen_saturation": "92%"}, "reviewState": "in_progress"},
    )
    assert response.status_code == 409, response.text
    assert "correction/amendment" in response.json()["detail"]
