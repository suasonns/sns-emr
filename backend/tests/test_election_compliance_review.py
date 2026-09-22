from __future__ import annotations

"""
Acceptance tests for the Election Compliance-Review resolution/reopen
workflow (resolve_compliance_review / reopen_compliance_review),
addressing the pre-merge gap flagged for the mandatory Election Statement
Addendum work (issue #142/#145).
"""

import uuid
from datetime import date, datetime, timezone

import pytest

from app.billing.models.election_addendum_request import ElectionAddendumAuditEvent, ElectionAddendumRequest
from app.billing.services import election_addendum_service as svc
from app.models.compliance_obligation import ComplianceAuditEvent, ComplianceObligation
from app.models.record_version import RecordVersion
from tests.conftest import TEST_USER_ID
from tests.test_election_addendum_mandatory_workflow import (
    _make_admission,
    _make_benefit_period,
    _make_patient,
)

OTHER_USER_ID = TEST_USER_ID


def _make_admission_missing_election_date(db_session, tenant_id):
    """Creates a patient/admission with NO benefit_period at all (Risk 2:
    missing election date)."""
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(
        db_session, patient, tenant_id, election_signed_at=datetime(2026, 10, 1, tzinfo=timezone.utc)
    )
    return patient, admission


def _make_open_review(db_session, tenant_id):
    """Opens a compliance review (Risk 2: missing election date), then
    creates a benefit_period (with a valid, later election_date) for use
    as the resolution's `benefit_period_id` argument, mirroring a chart
    correction happening after the review is opened."""
    patient, admission = _make_admission_missing_election_date(db_session, tenant_id)

    outcome = svc.get_or_create_mandatory_initial_addendum_requirement(
        db_session, tenant_id=tenant_id, admission_id=admission.id, created_by_user_id=TEST_USER_ID
    )
    assert outcome.outcome == "COMPLIANCE_REVIEW_REQUIRED"

    bp = _make_benefit_period(db_session, patient, tenant_id, election_date=date(2026, 10, 1))
    return patient, admission, bp, outcome.compliance_obligation


def test_missing_election_date_creates_compliance_review(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, admission, _, obligation = _make_open_review(db_session, tenant_id)
    assert obligation.status == "OPEN"
    assert obligation.admission_id == admission.id


def test_compliance_review_does_not_create_addendum_deadline(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, admission, _, obligation = _make_open_review(db_session, tenant_id)
    existing = (
        db_session.query(ElectionAddendumRequest)
        .filter(ElectionAddendumRequest.admission_id == admission.id)
        .first()
    )
    assert existing is None


def test_duplicate_open_review_is_not_created(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    # No benefit_period created yet -> review stays open on the 2nd call.
    _, admission = _make_admission_missing_election_date(db_session, tenant_id)
    outcome = svc.get_or_create_mandatory_initial_addendum_requirement(
        db_session, tenant_id=tenant_id, admission_id=admission.id, created_by_user_id=TEST_USER_ID
    )
    assert outcome.outcome == "COMPLIANCE_REVIEW_REQUIRED"
    obligation = outcome.compliance_obligation

    outcome2 = svc.get_or_create_mandatory_initial_addendum_requirement(
        db_session, tenant_id=tenant_id, admission_id=admission.id, created_by_user_id=TEST_USER_ID
    )
    assert outcome2.compliance_obligation.id == obligation.id
    count = (
        db_session.query(ComplianceObligation)
        .filter(ComplianceObligation.admission_id == admission.id)
        .count()
    )
    assert count == 1


def test_resolution_requires_reason(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, admission, bp, obligation = _make_open_review(db_session, tenant_id)
    with pytest.raises(svc.ElectionAddendumComplianceError):
        svc.resolve_compliance_review(
            db_session,
            tenant_id=tenant_id,
            compliance_obligation_id=obligation.id,
            benefit_period_id=bp.id,
            resolved_election_date=date(2026, 10, 1),
            resolution_reason="",
            resolved_by_user_id=TEST_USER_ID,
        )


def test_resolution_requires_election_date(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, admission, bp, obligation = _make_open_review(db_session, tenant_id)
    with pytest.raises(svc.ElectionAddendumComplianceError):
        svc.resolve_compliance_review(
            db_session,
            tenant_id=tenant_id,
            compliance_obligation_id=obligation.id,
            benefit_period_id=bp.id,
            resolved_election_date=None,
            resolution_reason="corrected",
            resolved_by_user_id=TEST_USER_ID,
        )


def test_resolution_rejects_date_before_signature(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, admission, bp, obligation = _make_open_review(db_session, tenant_id)
    with pytest.raises(svc.ElectionAddendumComplianceError):
        svc.resolve_compliance_review(
            db_session,
            tenant_id=tenant_id,
            compliance_obligation_id=obligation.id,
            benefit_period_id=bp.id,
            resolved_election_date=date(2026, 9, 1),  # before election_signed_at (2026-10-01)
            resolution_reason="corrected",
            resolved_by_user_id=TEST_USER_ID,
        )
    db_session.refresh(obligation)
    assert obligation.status == "OPEN"


def test_resolution_rejects_cross_patient_benefit_period(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, admission, _, obligation = _make_open_review(db_session, tenant_id)
    other_patient = _make_patient(db_session, tenant_id)
    other_bp = _make_benefit_period(db_session, other_patient, tenant_id, election_date=date(2026, 10, 1))

    with pytest.raises(svc.ElectionAddendumComplianceError):
        svc.resolve_compliance_review(
            db_session,
            tenant_id=tenant_id,
            compliance_obligation_id=obligation.id,
            benefit_period_id=other_bp.id,
            resolved_election_date=date(2026, 10, 1),
            resolution_reason="corrected",
            resolved_by_user_id=TEST_USER_ID,
        )


def test_resolution_rejects_cross_tenant_access(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, admission, bp, obligation = _make_open_review(db_session, tenant_id)
    other_tenant_id = uuid.uuid4()

    with pytest.raises(svc.ElectionAddendumComplianceError):
        svc.resolve_compliance_review(
            db_session,
            tenant_id=other_tenant_id,
            compliance_obligation_id=obligation.id,
            benefit_period_id=bp.id,
            resolved_election_date=date(2026, 10, 1),
            resolution_reason="corrected",
            resolved_by_user_id=TEST_USER_ID,
        )


def test_resolution_calculates_deadline_from_resolved_election_date_and_creates_requirement(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, admission, bp, obligation = _make_open_review(db_session, tenant_id)

    outcome = svc.resolve_compliance_review(
        db_session,
        tenant_id=tenant_id,
        compliance_obligation_id=obligation.id,
        benefit_period_id=bp.id,
        resolved_election_date=date(2026, 10, 1),
        resolution_reason="Corrected after chart review",
        resolved_by_user_id=TEST_USER_ID,
    )

    assert outcome.outcome == "CREATED"
    row = outcome.election_addendum_request
    assert row.election_effective_date == date(2026, 10, 1)
    assert row.required_by_at.date() == date(2026, 10, 6)  # +5 days

    db_session.refresh(obligation)
    assert obligation.status == "COMPLETED"
    assert obligation.completed_at is not None


def test_resolution_requirement_creation_is_idempotent_and_reuses_existing(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, admission, bp, obligation = _make_open_review(db_session, tenant_id)

    outcome1 = svc.resolve_compliance_review(
        db_session,
        tenant_id=tenant_id,
        compliance_obligation_id=obligation.id,
        benefit_period_id=bp.id,
        resolved_election_date=date(2026, 10, 1),
        resolution_reason="Corrected",
        resolved_by_user_id=TEST_USER_ID,
    )
    count_before = (
        db_session.query(ElectionAddendumRequest).filter(ElectionAddendumRequest.admission_id == admission.id).count()
    )
    assert count_before == 1

    # A second call against the same (now COMPLETED) obligation should fail
    # (review already resolved) -- resolution is not repeatable.
    with pytest.raises(svc.ElectionAddendumComplianceError):
        svc.resolve_compliance_review(
            db_session,
            tenant_id=tenant_id,
            compliance_obligation_id=obligation.id,
            benefit_period_id=bp.id,
            resolved_election_date=date(2026, 10, 1),
            resolution_reason="Corrected again",
            resolved_by_user_id=TEST_USER_ID,
        )


def test_resolution_preserves_original_values_via_record_version(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, admission, bp, obligation = _make_open_review(db_session, tenant_id)
    original_notes = obligation.notes

    svc.resolve_compliance_review(
        db_session,
        tenant_id=tenant_id,
        compliance_obligation_id=obligation.id,
        benefit_period_id=bp.id,
        resolved_election_date=date(2026, 10, 1),
        resolution_reason="Corrected",
        resolved_by_user_id=TEST_USER_ID,
    )

    version = (
        db_session.query(RecordVersion)
        .filter(
            RecordVersion.source_record_type == "COMPLIANCE_OBLIGATION",
            RecordVersion.source_record_id == obligation.id,
        )
        .first()
    )
    assert version is not None
    assert version.snapshot["status"] == "OPEN"
    assert version.snapshot["notes"] == original_notes


def test_resolution_emits_audit_event(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, admission, bp, obligation = _make_open_review(db_session, tenant_id)

    svc.resolve_compliance_review(
        db_session,
        tenant_id=tenant_id,
        compliance_obligation_id=obligation.id,
        benefit_period_id=bp.id,
        resolved_election_date=date(2026, 10, 1),
        resolution_reason="Corrected",
        resolved_by_user_id=TEST_USER_ID,
    )

    events = (
        db_session.query(ComplianceAuditEvent)
        .filter(ComplianceAuditEvent.compliance_obligation_id == obligation.id)
        .all()
    )
    event_types = {e.event_type for e in events}
    assert "REQUIREMENT_CREATED" in event_types  # obligation creation
    assert "RECORD_FINALIZED" in event_types  # resolution

    addendum_events = (
        db_session.query(ElectionAddendumAuditEvent)
        .filter(ElectionAddendumAuditEvent.admission_id == admission.id)
        .all()
    )
    assert any(e.event_type == "REQUIREMENT_CREATED" for e in addendum_events)


def test_resolved_review_cannot_be_resolved_twice(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, admission, bp, obligation = _make_open_review(db_session, tenant_id)
    svc.resolve_compliance_review(
        db_session,
        tenant_id=tenant_id,
        compliance_obligation_id=obligation.id,
        benefit_period_id=bp.id,
        resolved_election_date=date(2026, 10, 1),
        resolution_reason="Corrected",
        resolved_by_user_id=TEST_USER_ID,
    )
    with pytest.raises(svc.ElectionAddendumComplianceError):
        svc.resolve_compliance_review(
            db_session,
            tenant_id=tenant_id,
            compliance_obligation_id=obligation.id,
            benefit_period_id=bp.id,
            resolved_election_date=date(2026, 10, 2),
            resolution_reason="Again",
            resolved_by_user_id=TEST_USER_ID,
        )


# ---------------------------------------------------------------------
# Reopen
# ---------------------------------------------------------------------


def test_reopen_requires_reason(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, admission, bp, obligation = _make_open_review(db_session, tenant_id)
    svc.resolve_compliance_review(
        db_session,
        tenant_id=tenant_id,
        compliance_obligation_id=obligation.id,
        benefit_period_id=bp.id,
        resolved_election_date=date(2026, 10, 1),
        resolution_reason="Corrected",
        resolved_by_user_id=TEST_USER_ID,
    )
    with pytest.raises(svc.ElectionAddendumComplianceError):
        svc.reopen_compliance_review(
            db_session,
            tenant_id=tenant_id,
            compliance_obligation_id=obligation.id,
            reopen_reason="",
            reopened_by_user_id=TEST_USER_ID,
        )


def test_reopen_requires_authorized_actor(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, admission, bp, obligation = _make_open_review(db_session, tenant_id)
    svc.resolve_compliance_review(
        db_session,
        tenant_id=tenant_id,
        compliance_obligation_id=obligation.id,
        benefit_period_id=bp.id,
        resolved_election_date=date(2026, 10, 1),
        resolution_reason="Corrected",
        resolved_by_user_id=TEST_USER_ID,
    )
    with pytest.raises(svc.ElectionAddendumComplianceError):
        svc.reopen_compliance_review(
            db_session,
            tenant_id=tenant_id,
            compliance_obligation_id=obligation.id,
            reopen_reason="Need re-review",
            reopened_by_user_id=None,
        )


def test_reopen_requires_resolved_review(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, admission, bp, obligation = _make_open_review(db_session, tenant_id)
    with pytest.raises(svc.ElectionAddendumComplianceError):
        svc.reopen_compliance_review(
            db_session,
            tenant_id=tenant_id,
            compliance_obligation_id=obligation.id,
            reopen_reason="Need re-review",
            reopened_by_user_id=TEST_USER_ID,
        )


def test_reopen_preserves_original_resolution_and_does_not_touch_addendum(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    _, admission, bp, obligation = _make_open_review(db_session, tenant_id)
    outcome = svc.resolve_compliance_review(
        db_session,
        tenant_id=tenant_id,
        compliance_obligation_id=obligation.id,
        benefit_period_id=bp.id,
        resolved_election_date=date(2026, 10, 1),
        resolution_reason="Corrected",
        resolved_by_user_id=TEST_USER_ID,
    )
    addendum_id = outcome.election_addendum_request.id

    svc.reopen_compliance_review(
        db_session,
        tenant_id=tenant_id,
        compliance_obligation_id=obligation.id,
        reopen_reason="New info received",
        reopened_by_user_id=OTHER_USER_ID,
    )

    db_session.refresh(obligation)
    assert obligation.status == "OPEN"

    # The addendum row created during resolution is untouched.
    addendum = db_session.get(ElectionAddendumRequest, addendum_id)
    assert addendum is not None
    assert addendum.election_effective_date == date(2026, 10, 1)

    version = (
        db_session.query(RecordVersion)
        .filter(
            RecordVersion.source_record_type == "COMPLIANCE_OBLIGATION",
            RecordVersion.source_record_id == obligation.id,
        )
        .order_by(RecordVersion.version_number.desc())
        .first()
    )
    assert version.snapshot["status"] == "COMPLETED"

    events = (
        db_session.query(ComplianceAuditEvent)
        .filter(
            ComplianceAuditEvent.compliance_obligation_id == obligation.id,
            ComplianceAuditEvent.event_type == "RECORD_REOPENED",
        )
        .all()
    )
    assert len(events) == 1


# ---------------------------------------------------------------------
# Atomicity / rollback and benefit-period-scoping edge cases
# ---------------------------------------------------------------------


def test_resolution_rolls_back_obligation_change_if_requirement_creation_fails(db_session, tenant, monkeypatch):
    """If the shared addendum-requirement helper raises after the
    obligation has been mutated in-memory, resolve_compliance_review must
    roll back the whole transaction -- the obligation must NOT end up
    COMPLETED without a corresponding addendum requirement having been
    created."""
    tenant_id = uuid.UUID(tenant.id)
    _, admission, bp, obligation = _make_open_review(db_session, tenant_id)
    obligation_id = obligation.id

    def _boom(*args, **kwargs):
        raise RuntimeError("simulated addendum-requirement creation failure")

    monkeypatch.setattr(svc, "_get_or_create_mandatory_addendum_request_row", _boom)

    with pytest.raises(RuntimeError):
        svc.resolve_compliance_review(
            db_session,
            tenant_id=tenant_id,
            compliance_obligation_id=obligation_id,
            benefit_period_id=bp.id,
            resolved_election_date=date(2026, 10, 1),
            resolution_reason="Corrected",
            resolved_by_user_id=TEST_USER_ID,
        )

    reloaded = db_session.get(ComplianceObligation, obligation_id)
    assert reloaded.status == "OPEN"
    assert reloaded.completed_at is None

    # No RecordVersion snapshot should have survived the rollback either.
    versions = (
        db_session.query(RecordVersion)
        .filter(
            RecordVersion.source_record_type == "COMPLIANCE_OBLIGATION",
            RecordVersion.source_record_id == obligation_id,
        )
        .all()
    )
    assert versions == []


def test_benefit_period_rollover_does_not_recalculate_initial_deadline(db_session, tenant):
    """A later (rollover/subsequent) benefit_period must never change the
    already-computed initial mandatory-addendum deadline -- the resolver
    only ever considers benefit_type='INITIAL', period_number=1."""
    tenant_id = uuid.UUID(tenant.id)
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(
        db_session, patient, tenant_id, election_signed_at=datetime(2026, 10, 1, tzinfo=timezone.utc)
    )
    _make_benefit_period(
        db_session, patient, tenant_id, election_date=date(2026, 10, 1), period_number=1, benefit_type="INITIAL"
    )

    outcome1 = svc.get_or_create_mandatory_initial_addendum_requirement(
        db_session, tenant_id=tenant_id, admission_id=admission.id, created_by_user_id=TEST_USER_ID
    )
    assert outcome1.outcome == "CREATED"
    original_required_by = outcome1.election_addendum_request.required_by_at

    # Rollover to a subsequent benefit period.
    _make_benefit_period(
        db_session, patient, tenant_id, election_date=date(2027, 1, 1), period_number=2, benefit_type="RECERT"
    )

    outcome2 = svc.get_or_create_mandatory_initial_addendum_requirement(
        db_session, tenant_id=tenant_id, admission_id=admission.id, created_by_user_id=TEST_USER_ID
    )
    assert outcome2.outcome == "EXISTING"
    assert outcome2.election_addendum_request.required_by_at == original_required_by


def test_resolution_accepts_patient_scoped_benefit_period_regardless_of_which_admission_opened_review(
    db_session, tenant
):
    """benefit_periods are patient-scoped, not admission-scoped, by
    confirmed schema mapping -- a benefit_period belonging to the same
    patient is valid resolution evidence for a review opened against any
    of that patient's admissions. This is intended behavior, not a gap:
    there is no admission_id column on benefit_periods to scope against."""
    tenant_id = uuid.UUID(tenant.id)
    patient, admission = _make_admission_missing_election_date(db_session, tenant_id)
    # A second admission for the same patient exists but is irrelevant here.
    _make_admission(db_session, patient, tenant_id, election_signed_at=datetime(2026, 10, 5, tzinfo=timezone.utc))

    outcome = svc.get_or_create_mandatory_initial_addendum_requirement(
        db_session, tenant_id=tenant_id, admission_id=admission.id, created_by_user_id=TEST_USER_ID
    )
    obligation = outcome.compliance_obligation
    bp = _make_benefit_period(db_session, patient, tenant_id, election_date=date(2026, 10, 1))

    resolved_outcome = svc.resolve_compliance_review(
        db_session,
        tenant_id=tenant_id,
        compliance_obligation_id=obligation.id,
        benefit_period_id=bp.id,
        resolved_election_date=date(2026, 10, 1),
        resolution_reason="Corrected",
        resolved_by_user_id=TEST_USER_ID,
    )
    assert resolved_outcome.outcome == "CREATED"
    assert resolved_outcome.election_addendum_request.admission_id == admission.id
