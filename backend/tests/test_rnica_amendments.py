from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.core.security import create_access_token
from app.models.patient import Patient
from app.models.rnica_assessment import RnicaAssessment
from app.models.user import User
from tests.conftest import _test_tenant_id


def _make_patient(db_session, tenant_id):
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"AMEND-{uuid.uuid4().hex[:12]}",
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="Hospice qualifying diagnosis",
        status="ACTIVE",
        admission_status="PRE_REFERRAL",
        created_by=None,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _make_rnica_assessment(db_session, patient, tenant_id, locked=True, form_data=None):
    record = RnicaAssessment(
        id=uuid.uuid4(),
        patient_id=patient.id,
        tenant_id=uuid.UUID(str(tenant_id)),
        form_data=form_data or {"diagnoses": {"clinicalNarrative": "Original signed narrative."}},
        locked=locked,
    )
    db_session.add(record)
    db_session.commit()
    return record


def _supervisor_headers(db_session, role="DPCS"):
    """A distinct user (not TEST_USER_ID) so self-approval tests are
    meaningful -- every stock fixture in conftest reuses TEST_USER_ID with
    only the JWT role claim varying, which would make an approver
    indistinguishable from the submitting RN.
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
def test_submit_validates_request_source_and_defaults_to_staff(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient = _make_patient(db_session, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id, locked=True)

    bad_source = client.post(
        f"/visits/rnica/{record.id}/correction-request",
        json={
            "amendment_category": "CLINICAL_CORRECTION",
            "reason_code": "OMITTED_FINDING",
            "requested_change": "Something.",
            "request_source": "NOT_A_SOURCE",
        },
        headers=rn_headers,
    )
    assert bad_source.status_code == 400, bad_source.text

    default_source_resp = client.post(
        f"/visits/rnica/{record.id}/correction-request",
        json={
            "amendment_category": "CLINICAL_CORRECTION",
            "reason_code": "OMITTED_FINDING",
            "requested_change": "Something without an explicit request_source.",
        },
        headers=rn_headers,
    )
    assert default_source_resp.status_code == 200, default_source_resp.text
    assert default_source_resp.json()["requestSource"] == "STAFF"

    patient_source_resp = client.post(
        f"/visits/rnica/{record.id}/correction-request",
        json={
            "amendment_category": "CLARIFICATION",
            "reason_code": "CLARIFICATION_NEEDED",
            "requested_change": "Family requested clarification of documented findings.",
            "request_source": "representative",
        },
        headers=rn_headers,
    )
    assert patient_source_resp.status_code == 200, patient_source_resp.text
    assert patient_source_resp.json()["requestSource"] == "REPRESENTATIVE"


@pytest.mark.integration
def test_submit_requires_locked_assessment(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient = _make_patient(db_session, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id, locked=False)

    resp = client.post(
        f"/visits/rnica/{record.id}/correction-request",
        json={
            "amendment_category": "CLINICAL_CORRECTION",
            "reason_code": "OMITTED_FINDING",
            "requested_change": "Add missing pain assessment finding.",
        },
        headers=rn_headers,
    )
    assert resp.status_code == 400, resp.text


@pytest.mark.integration
def test_submit_validates_category_reason_and_blank_text(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient = _make_patient(db_session, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id, locked=True)

    bad_category = client.post(
        f"/visits/rnica/{record.id}/correction-request",
        json={
            "amendment_category": "NOT_A_CATEGORY",
            "reason_code": "OMITTED_FINDING",
            "requested_change": "Something.",
        },
        headers=rn_headers,
    )
    assert bad_category.status_code == 400, bad_category.text

    bad_reason = client.post(
        f"/visits/rnica/{record.id}/correction-request",
        json={
            "amendment_category": "CLINICAL_CORRECTION",
            "reason_code": "NOT_A_REASON",
            "requested_change": "Something.",
        },
        headers=rn_headers,
    )
    assert bad_reason.status_code == 400, bad_reason.text

    blank_text = client.post(
        f"/visits/rnica/{record.id}/correction-request",
        json={
            "amendment_category": "CLINICAL_CORRECTION",
            "reason_code": "OMITTED_FINDING",
            "requested_change": "   ",
        },
        headers=rn_headers,
    )
    assert blank_text.status_code == 422, blank_text.text


@pytest.mark.integration
def test_full_amendment_workflow_approve_and_deny_never_mutate_original(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient = _make_patient(db_session, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id, locked=True)
    original_form_data = dict(record.form_data)

    supervisor_headers, supervisor_id = _supervisor_headers(db_session, role="DPCS")

    # --- Submit -----------------------------------------------------------
    create_resp = client.post(
        f"/visits/rnica/{record.id}/correction-request",
        json={
            "section_reference": "section_10_clinical_narrative",
            "amendment_category": "CLINICAL_CORRECTION",
            "reason_code": "OMITTED_FINDING",
            "requested_change": "Add documented pain assessment finding omitted at signing.",
            "proposed_value": "Pain assessed at 6/10, controlled with hydromorphone.",
        },
        headers=rn_headers,
    )
    assert create_resp.status_code == 200, create_resp.text
    created = create_resp.json()
    assert created["status"] == "PENDING"
    assert created["amendmentCategory"] == "CLINICAL_CORRECTION"
    assert created["reasonCode"] == "OMITTED_FINDING"
    assert created["sectionReference"] == "section_10_clinical_narrative"
    amendment_id = created["id"]

    # --- List ---------------------------------------------------------------
    list_resp = client.get(f"/visits/rnica/{record.id}/amendments", headers=rn_headers)
    assert list_resp.status_code == 200, list_resp.text
    assert any(a["id"] == amendment_id for a in list_resp.json()["amendments"])

    # --- Non-approval role cannot approve -----------------------------------
    forbidden_resp = client.post(
        f"/visits/rnica/{record.id}/amendments/{amendment_id}/approve",
        headers=rn_headers,
    )
    assert forbidden_resp.status_code == 403, forbidden_resp.text

    # --- Approve by a distinct DPCS reviewer --------------------------------
    approve_resp = client.post(
        f"/visits/rnica/{record.id}/amendments/{amendment_id}/approve",
        headers=supervisor_headers,
    )
    assert approve_resp.status_code == 200, approve_resp.text
    approved = approve_resp.json()
    assert approved["status"] == "APPROVED"
    assert approved["decisionUserId"] == str(supervisor_id)
    assert approved["decisionTimestamp"] is not None

    # --- Original assessment content is never mutated -----------------------
    db_session.refresh(record)
    assert record.form_data == original_form_data
    assert record.locked is True

    # --- Cannot re-decide an already-decided amendment ----------------------
    redecide_resp = client.post(
        f"/visits/rnica/{record.id}/amendments/{amendment_id}/approve",
        headers=supervisor_headers,
    )
    assert redecide_resp.status_code == 400, redecide_resp.text


@pytest.mark.integration
def test_deny_requires_reason_and_supports_case_manager_and_supervisor_roles(client, db_session, rn_headers):
    tenant_id = db_session.info.get("tenant_id")
    patient = _make_patient(db_session, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id, locked=True)

    for role in ("CASE_MANAGER", "SUPERVISOR", "DPCS_DESIGNEE"):
        create_resp = client.post(
            f"/visits/rnica/{record.id}/correction-request",
            json={
                "amendment_category": "DOCUMENTATION_ERROR",
                "reason_code": "INCORRECT_VALUE",
                "requested_change": f"Correct value for {role} review.",
            },
            headers=rn_headers,
        )
        assert create_resp.status_code == 200, create_resp.text
        amendment_id = create_resp.json()["id"]

        reviewer_headers, reviewer_id = _supervisor_headers(db_session, role=role)

        missing_reason_resp = client.post(
            f"/visits/rnica/{record.id}/amendments/{amendment_id}/deny",
            json={"decision_reason": "   "},
            headers=reviewer_headers,
        )
        assert missing_reason_resp.status_code == 422, missing_reason_resp.text

        deny_resp = client.post(
            f"/visits/rnica/{record.id}/amendments/{amendment_id}/deny",
            json={"decision_reason": f"Not supported by documentation ({role})."},
            headers=reviewer_headers,
        )
        assert deny_resp.status_code == 200, deny_resp.text
        denied = deny_resp.json()
        assert denied["status"] == "DENIED"
        assert denied["decisionUserId"] == str(reviewer_id)
        assert denied["decisionReason"] == f"Not supported by documentation ({role})."


@pytest.mark.integration
def test_submitter_cannot_approve_or_deny_own_amendment(client, db_session):
    tenant_id = db_session.info.get("tenant_id")
    patient = _make_patient(db_session, tenant_id)
    record = _make_rnica_assessment(db_session, patient, tenant_id, locked=True)

    # A single DPCS clinician both submits and attempts to review their own
    # amendment -- must be rejected even though their role otherwise
    # qualifies as review authority.
    dpcs_headers, _dpcs_id = _supervisor_headers(db_session, role="DPCS")

    create_resp = client.post(
        f"/visits/rnica/{record.id}/correction-request",
        json={
            "amendment_category": "CLARIFICATION",
            "reason_code": "CLARIFICATION_NEEDED",
            "requested_change": "Clarify caregiver support documentation.",
        },
        headers=dpcs_headers,
    )
    assert create_resp.status_code == 200, create_resp.text
    amendment_id = create_resp.json()["id"]

    self_approve_resp = client.post(
        f"/visits/rnica/{record.id}/amendments/{amendment_id}/approve",
        headers=dpcs_headers,
    )
    assert self_approve_resp.status_code == 400, self_approve_resp.text

    self_deny_resp = client.post(
        f"/visits/rnica/{record.id}/amendments/{amendment_id}/deny",
        json={"decision_reason": "Self review not permitted."},
        headers=dpcs_headers,
    )
    assert self_deny_resp.status_code == 400, self_deny_resp.text
