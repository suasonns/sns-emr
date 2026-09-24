from __future__ import annotations

"""
Acceptance tests for the item-level relatedness-review workflow
(REQUIREMENT_CREATED -> PENDING_RELATEDNESS_REVIEW -> READY_FOR_GENERATION
-> ADDENDUM_GENERATED -> ADDENDUM_FURNISHED, with EXCEPTION_CLOSED
reachable from any open state). Workflow-owner decision: the operational
risk is delayed relatedness determination, not document finalization --
these tests focus on the state-machine transitions, item-level review
blocking rules, the compliance clock never being stopped by review/
generation, and audit-event emission for every mutation.
"""

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from app.billing.models.election_addendum_request import (
    ElectionAddendumAuditEvent,
    ElectionAddendumDetermination,
    ElectionAddendumRequest,
)
from app.billing.services import election_addendum_service as svc
from app.models.admission import Admission
from app.models.benefit_period import BenefitPeriod
from app.models.patient import Patient
from tests.conftest import TEST_USER_ID


def _make_patient(db_session, tenant_id):
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"REL-{uuid.uuid4().hex[:12]}",
        date_of_birth=date(1945, 3, 2),
        primary_diagnosis="End stage renal disease",
        status="ACTIVE",
        admission_status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _make_admission(db_session, patient, tenant_id):
    admission = Admission(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient.id,
        admission_date=datetime(2026, 10, 1, tzinfo=timezone.utc),
        effective_date=datetime(2026, 10, 1, tzinfo=timezone.utc),
        election_signed_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        soc_date=datetime(2026, 10, 1, tzinfo=timezone.utc),
        status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(admission)
    db_session.commit()
    return admission


def _make_benefit_period(db_session, patient, tenant_id):
    bp = BenefitPeriod(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient.id,
        benefit_type="INITIAL",
        period_number=1,
        election_date=date(2026, 10, 1),
        start_date=date(2026, 10, 1),
        created_by=TEST_USER_ID,
    )
    db_session.add(bp)
    db_session.commit()
    return bp


def _make_requirement(db_session, tenant_id):
    """Build a REQUIREMENT_CREATED addendum row directly (bypassing the
    mandatory-rule resolution service already covered by
    test_election_addendum_mandatory_workflow.py) so these tests focus on
    the relatedness-review state machine."""
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id)
    bp = _make_benefit_period(db_session, patient, tenant_id)
    row = ElectionAddendumRequest(
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
    db_session.add(row)
    db_session.commit()
    return row


def _audit_event_types(db_session, addendum_request_id):
    rows = (
        db_session.query(ElectionAddendumAuditEvent)
        .filter(ElectionAddendumAuditEvent.addendum_request_id == addendum_request_id)
        .order_by(ElectionAddendumAuditEvent.created_at)
        .all()
    )
    return [r.event_type for r in rows]


# ---------------------------------------------------------------------
# State machine: happy path
# ---------------------------------------------------------------------


def test_full_relatedness_review_happy_path(db_session, tenant):
    tenant_id = tenant.id
    req = _make_requirement(db_session, tenant_id)

    svc.start_relatedness_review(
        db_session,
        addendum_request=req,
        reason="Dialysis and specialty medications require relatedness review",
        actor_user_id=TEST_USER_ID,
    )
    assert req.workflow_status == "PENDING_RELATEDNESS_REVIEW"
    assert req.relatedness_review_started_at is not None

    item = svc.add_relatedness_item(
        db_session,
        addendum_request=req,
        determination_type="DIALYSIS_TREATMENT",
        description="Ongoing hemodialysis",
        effective_date=date(2026, 10, 2),
        current_provider_or_supplier="Acme Dialysis Center",
        actor_user_id=TEST_USER_ID,
    )
    assert item.relationship_status == "PENDING_REVIEW"
    assert item.coverage_status is None

    svc.record_relatedness_item_determination(
        db_session,
        addendum_request=req,
        item=item,
        relationship_status="UNRELATED",
        coverage_status="NOT_COVERED",
        coverage_owner="NON_HOSPICE_MEDICARE",
        clinical_rationale="Dialysis for ESRD is not related to the terminal hospice diagnosis",
        actor_user_id=TEST_USER_ID,
    )
    assert item.relationship_status == "UNRELATED"
    assert item.reviewed_by_user_id == TEST_USER_ID

    svc.complete_relatedness_review(
        db_session,
        addendum_request=req,
        clinical_rationale="All disputed items reviewed and determined",
        actor_user_id=TEST_USER_ID,
    )
    assert req.workflow_status == "READY_FOR_GENERATION"

    svc.generate_addendum_document(
        db_session,
        addendum_request=req,
        document_reference="doc-ref-001",
        document_version=1,
        actor_user_id=TEST_USER_ID,
    )
    assert req.workflow_status == "ADDENDUM_GENERATED"
    assert req.generated_at is not None

    svc.record_furnishing(
        db_session,
        addendum_request=req,
        furnished_at=req.generated_at + timedelta(hours=1),
        furnished_to="PATIENT",
        furnishing_method="IN_PERSON",
        bfcc_qio_information_furnished=True,
        actor_user_id=TEST_USER_ID,
    )
    assert req.workflow_status == "ADDENDUM_FURNISHED"

    events = _audit_event_types(db_session, req.id)
    assert events == [
        "RELATEDNESS_REVIEW_STARTED",
        "RELATEDNESS_ITEM_CREATED",
        "RELATEDNESS_ITEM_DETERMINED",
        "RELATEDNESS_DETERMINED",
        "ADDENDUM_GENERATED",
        "ADDENDUM_FURNISHED",
    ]


# ---------------------------------------------------------------------
# Blocking rules
# ---------------------------------------------------------------------


def test_cannot_complete_review_with_pending_item(db_session, tenant):
    req = _make_requirement(db_session, tenant.id)
    svc.start_relatedness_review(db_session, addendum_request=req, reason="unusual case", actor_user_id=TEST_USER_ID)
    svc.add_relatedness_item(
        db_session,
        addendum_request=req,
        determination_type="DRUG",
        description="Specialty medication",
        effective_date=date(2026, 10, 2),
        actor_user_id=TEST_USER_ID,
    )
    with pytest.raises(svc.ElectionAddendumComplianceError):
        svc.complete_relatedness_review(
            db_session, addendum_request=req, clinical_rationale="done", actor_user_id=TEST_USER_ID
        )


def test_cannot_complete_review_with_undetermined_coverage_owner(db_session, tenant):
    req = _make_requirement(db_session, tenant.id)
    svc.start_relatedness_review(db_session, addendum_request=req, reason="unusual case", actor_user_id=TEST_USER_ID)
    item = svc.add_relatedness_item(
        db_session,
        addendum_request=req,
        determination_type="DME",
        description="Hospital bed",
        effective_date=date(2026, 10, 2),
        actor_user_id=TEST_USER_ID,
    )
    with pytest.raises(svc.ElectionAddendumComplianceError):
        svc.record_relatedness_item_determination(
            db_session,
            addendum_request=req,
            item=item,
            relationship_status="RELATED",
            coverage_status="COVERED",
            coverage_owner="UNDETERMINED",
            actor_user_id=TEST_USER_ID,
        )


def test_unrelated_determination_requires_clinical_rationale(db_session, tenant):
    req = _make_requirement(db_session, tenant.id)
    svc.start_relatedness_review(db_session, addendum_request=req, reason="unusual case", actor_user_id=TEST_USER_ID)
    item = svc.add_relatedness_item(
        db_session,
        addendum_request=req,
        determination_type="SUPPLY",
        description="Wound care supplies",
        effective_date=date(2026, 10, 2),
        actor_user_id=TEST_USER_ID,
    )
    with pytest.raises(svc.ElectionAddendumComplianceError):
        svc.record_relatedness_item_determination(
            db_session,
            addendum_request=req,
            item=item,
            relationship_status="UNRELATED",
            coverage_status="NOT_COVERED",
            coverage_owner="OTHER_PAYER",
            clinical_rationale=None,
            actor_user_id=TEST_USER_ID,
        )


def test_physician_review_required_blocks_completion_until_done(db_session, tenant):
    req = _make_requirement(db_session, tenant.id)
    svc.start_relatedness_review(db_session, addendum_request=req, reason="unusual case", actor_user_id=TEST_USER_ID)
    item = svc.add_relatedness_item(
        db_session,
        addendum_request=req,
        determination_type="DIALYSIS_TREATMENT",
        description="Dialysis",
        effective_date=date(2026, 10, 2),
        actor_user_id=TEST_USER_ID,
    )
    svc.record_relatedness_item_determination(
        db_session,
        addendum_request=req,
        item=item,
        relationship_status="UNRELATED",
        coverage_status="NOT_COVERED",
        coverage_owner="NON_HOSPICE_MEDICARE",
        clinical_rationale="Not related to terminal diagnosis",
        actor_user_id=TEST_USER_ID,
    )
    svc.request_physician_review(
        db_session, addendum_request=req, physician_user_id=TEST_USER_ID, actor_user_id=TEST_USER_ID
    )
    # Requirement clock stays PENDING_RELATEDNESS_REVIEW -- physician
    # request does not stop or advance the compliance clock.
    assert req.workflow_status == "PENDING_RELATEDNESS_REVIEW"
    assert req.required_by_at == datetime(2026, 10, 6, tzinfo=timezone.utc)

    with pytest.raises(svc.ElectionAddendumComplianceError):
        svc.complete_relatedness_review(
            db_session, addendum_request=req, clinical_rationale="done", actor_user_id=TEST_USER_ID
        )

    svc.complete_physician_review(
        db_session, addendum_request=req, rationale="Physician confirms dialysis unrelated", actor_user_id=TEST_USER_ID
    )
    svc.complete_relatedness_review(
        db_session, addendum_request=req, clinical_rationale="Review complete", actor_user_id=TEST_USER_ID
    )
    assert req.workflow_status == "READY_FOR_GENERATION"


def test_generation_blocked_before_review_complete(db_session, tenant):
    req = _make_requirement(db_session, tenant.id)
    with pytest.raises(svc.ElectionAddendumComplianceError):
        svc.generate_addendum_document(
            db_session,
            addendum_request=req,
            document_reference="doc-ref",
            document_version=1,
            actor_user_id=TEST_USER_ID,
        )


def test_furnishing_blocked_before_generation(db_session, tenant):
    req = _make_requirement(db_session, tenant.id)
    with pytest.raises(svc.ElectionAddendumComplianceError):
        svc.record_furnishing(
            db_session,
            addendum_request=req,
            furnished_at=datetime.now(timezone.utc),
            furnished_to="PATIENT",
            furnishing_method="IN_PERSON",
            bfcc_qio_information_furnished=True,
            actor_user_id=TEST_USER_ID,
        )


def test_furnished_at_before_generated_at_rejected(db_session, tenant):
    req = _make_requirement(db_session, tenant.id)
    svc.start_relatedness_review(db_session, addendum_request=req, reason="r", actor_user_id=TEST_USER_ID)
    item = svc.add_relatedness_item(
        db_session,
        addendum_request=req,
        determination_type="CONDITION",
        description="condition",
        effective_date=date(2026, 10, 2),
        actor_user_id=TEST_USER_ID,
    )
    svc.record_relatedness_item_determination(
        db_session,
        addendum_request=req,
        item=item,
        relationship_status="RELATED",
        coverage_status="COVERED",
        coverage_owner="HOSPICE",
        actor_user_id=TEST_USER_ID,
    )
    svc.complete_relatedness_review(db_session, addendum_request=req, clinical_rationale="ok", actor_user_id=TEST_USER_ID)
    svc.generate_addendum_document(
        db_session, addendum_request=req, document_reference="doc-1", document_version=1, actor_user_id=TEST_USER_ID
    )
    with pytest.raises(svc.ElectionAddendumComplianceError):
        svc.record_furnishing(
            db_session,
            addendum_request=req,
            furnished_at=req.generated_at - timedelta(hours=1),
            furnished_to="PATIENT",
            furnishing_method="IN_PERSON",
            bfcc_qio_information_furnished=True,
            actor_user_id=TEST_USER_ID,
        )


# ---------------------------------------------------------------------
# Clock never stopped by review/generation; only furnishing or exception
# ---------------------------------------------------------------------


def test_pending_review_does_not_change_required_by_at(db_session, tenant):
    req = _make_requirement(db_session, tenant.id)
    original_deadline = req.required_by_at
    svc.start_relatedness_review(db_session, addendum_request=req, reason="r", actor_user_id=TEST_USER_ID)
    assert req.required_by_at == original_deadline


def test_exception_closes_requirement_from_open_state(db_session, tenant):
    req = _make_requirement(db_session, tenant.id)
    svc.record_exception(
        db_session,
        addendum_request=req,
        exception_type="PATIENT_DIED",
        exception_occurred_at=datetime.now(timezone.utc),
        reason="Patient expired before furnishing was possible",
        actor_user_id=TEST_USER_ID,
    )
    assert req.workflow_status == "EXCEPTION_CLOSED"
    assert "EXCEPTION_RECORDED" in _audit_event_types(db_session, req.id)


def test_exception_blocked_once_already_furnished(db_session, tenant):
    req = _make_requirement(db_session, tenant.id)
    svc.start_relatedness_review(db_session, addendum_request=req, reason="r", actor_user_id=TEST_USER_ID)
    item = svc.add_relatedness_item(
        db_session,
        addendum_request=req,
        determination_type="CONDITION",
        description="c",
        effective_date=date(2026, 10, 2),
        actor_user_id=TEST_USER_ID,
    )
    svc.record_relatedness_item_determination(
        db_session,
        addendum_request=req,
        item=item,
        relationship_status="RELATED",
        coverage_status="COVERED",
        coverage_owner="HOSPICE",
        actor_user_id=TEST_USER_ID,
    )
    svc.complete_relatedness_review(db_session, addendum_request=req, clinical_rationale="ok", actor_user_id=TEST_USER_ID)
    svc.generate_addendum_document(
        db_session, addendum_request=req, document_reference="doc-1", document_version=1, actor_user_id=TEST_USER_ID
    )
    svc.record_furnishing(
        db_session,
        addendum_request=req,
        furnished_at=req.generated_at,
        furnished_to="PATIENT",
        furnishing_method="IN_PERSON",
        bfcc_qio_information_furnished=True,
        actor_user_id=TEST_USER_ID,
    )
    with pytest.raises(svc.ElectionAddendumComplianceError):
        svc.record_exception(
            db_session,
            addendum_request=req,
            exception_type="PATIENT_DIED",
            exception_occurred_at=datetime.now(timezone.utc),
            reason="too late",
            actor_user_id=TEST_USER_ID,
        )


# ---------------------------------------------------------------------
# Acknowledgment
# ---------------------------------------------------------------------


def test_acknowledgment_refused_requires_reason(db_session, tenant):
    req = _make_requirement(db_session, tenant.id)
    with pytest.raises(svc.ElectionAddendumComplianceError):
        svc.record_acknowledgment(
            db_session,
            addendum_request=req,
            acknowledgment_status="REFUSED",
            signature_exception_reason=None,
            actor_user_id=TEST_USER_ID,
        )


def test_acknowledgment_signed_by_representative(db_session, tenant):
    req = _make_requirement(db_session, tenant.id)
    svc.record_acknowledgment(
        db_session,
        addendum_request=req,
        acknowledgment_status="SIGNED_BY_REPRESENTATIVE",
        acknowledgment_document_reference="packet-ref-1",
        actor_user_id=TEST_USER_ID,
    )
    assert req.acknowledgment_status == "SIGNED_BY_REPRESENTATIVE"
    assert req.acknowledgment_at is not None
    assert "ACKNOWLEDGMENT_RECORDED" in _audit_event_types(db_session, req.id)


# ---------------------------------------------------------------------
# Versioned updates
# ---------------------------------------------------------------------


def test_poc_change_creates_new_version_and_preserves_prior(db_session, tenant):
    req = _make_requirement(db_session, tenant.id)
    svc.start_relatedness_review(db_session, addendum_request=req, reason="r", actor_user_id=TEST_USER_ID)
    item = svc.add_relatedness_item(
        db_session,
        addendum_request=req,
        determination_type="CONDITION",
        description="c",
        effective_date=date(2026, 10, 2),
        actor_user_id=TEST_USER_ID,
    )
    svc.record_relatedness_item_determination(
        db_session,
        addendum_request=req,
        item=item,
        relationship_status="RELATED",
        coverage_status="COVERED",
        coverage_owner="HOSPICE",
        actor_user_id=TEST_USER_ID,
    )
    svc.complete_relatedness_review(db_session, addendum_request=req, clinical_rationale="ok", actor_user_id=TEST_USER_ID)
    svc.generate_addendum_document(
        db_session, addendum_request=req, document_reference="doc-1", document_version=1, actor_user_id=TEST_USER_ID
    )
    svc.record_furnishing(
        db_session,
        addendum_request=req,
        furnished_at=req.generated_at,
        furnished_to="PATIENT",
        furnishing_method="IN_PERSON",
        bfcc_qio_information_furnished=True,
        actor_user_id=TEST_USER_ID,
    )

    new_row = svc.create_addendum_update_for_relatedness_change(
        db_session,
        prior_addendum_request=req,
        poc_change_date=date(2026, 10, 10),
        created_by_user_id=TEST_USER_ID,
    )

    assert new_row.version_number == req.version_number + 1
    assert new_row.supersedes_request_id == req.id
    assert new_row.workflow_status == "REQUIREMENT_CREATED"
    assert new_row.required_by_at == datetime(2026, 10, 13, tzinfo=timezone.utc)

    # Prior furnished version remains retrievable and untouched.
    db_session.refresh(req)
    assert req.workflow_status == "ADDENDUM_FURNISHED"
    assert req.document_reference == "doc-1"
    assert "ADDENDUM_SUPERSEDED" in _audit_event_types(db_session, req.id)


# ---------------------------------------------------------------------
# Tenant isolation
# ---------------------------------------------------------------------


def test_cross_tenant_addendum_not_visible(db_session, tenant):
    other_tenant_id = uuid.uuid4()
    req = _make_requirement(db_session, tenant.id)

    found = (
        db_session.query(ElectionAddendumRequest)
        .filter(
            ElectionAddendumRequest.tenant_id == other_tenant_id,
            ElectionAddendumRequest.id == req.id,
        )
        .first()
    )
    assert found is None

    found_correct_tenant = (
        db_session.query(ElectionAddendumRequest)
        .filter(
            ElectionAddendumRequest.tenant_id == tenant.id,
            ElectionAddendumRequest.id == req.id,
        )
        .first()
    )
    assert found_correct_tenant is not None
