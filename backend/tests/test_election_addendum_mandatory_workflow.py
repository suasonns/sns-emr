from __future__ import annotations

"""
Acceptance tests for the CMS FY2027 mandatory Election Statement Addendum
workflow (issue #142) and the shared compliance-migration checklist
(issue #145): schema-protection guarantees plus the election-date
resolution/creation service behavior (Risks 1-3 from the workflow-owner's
Final Compliance Review).
"""

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.billing.models.election_addendum_request import ElectionAddendumRequest
from app.billing.services import election_addendum_service as svc
from app.models.admission import Admission
from app.models.benefit_period import BenefitPeriod
from app.models.compliance_obligation import ComplianceObligation
from app.models.patient import Patient
from tests.conftest import TEST_USER_ID


def _make_patient(db_session, tenant_id):
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"ADD-{uuid.uuid4().hex[:12]}",
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="Adult failure to thrive",
        status="ACTIVE",
        admission_status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _make_admission(db_session, patient, tenant_id, *, election_signed_at=None):
    admission = Admission(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient.id,
        admission_date=election_signed_at or datetime(2026, 10, 1, tzinfo=timezone.utc),
        effective_date=election_signed_at or datetime(2026, 10, 1, tzinfo=timezone.utc),
        election_signed_at=election_signed_at,
        soc_date=election_signed_at or datetime(2026, 10, 1, tzinfo=timezone.utc),
        status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(admission)
    db_session.commit()
    return admission


def _make_benefit_period(db_session, patient, tenant_id, *, election_date, period_number=1, benefit_type="INITIAL"):
    bp = BenefitPeriod(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient.id,
        benefit_type=benefit_type,
        period_number=period_number,
        election_date=election_date,
        start_date=election_date,
        created_by=TEST_USER_ID,
    )
    db_session.add(bp)
    db_session.commit()
    return bp


# ---------------------------------------------------------------------
# Existing-schema protection (issue #145 checklist)
# ---------------------------------------------------------------------


def test_no_forbidden_parallel_tables_exist(db_session):
    rows = db_session.execute(
        text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name IN "
            "('episodes', 'hospice_elections', 'hope_records', 'audit_event', 'idg_follow_ups', "
            "'hospice_election_addendum', 'hope_submission_obligation')"
        )
    ).fetchall()
    assert rows == []


@pytest.mark.parametrize(
    "table_name",
    [
        "election_addendum_requests",
        "election_addendum_determinations",
        "election_addendum_audit_events",
        "compliance_obligations",
        "compliance_audit_events",
        "patient_response_events",
        "nurse_response_assignments",
        "interim_patient_support",
        "response_interventions",
        "patient_response_audit_events",
        "clinical_outcome_records",
        "rnica_hope_submission_attempts",
        "record_versions",
    ],
)
def test_new_tables_have_tenant_id(db_session, table_name):
    row = db_session.execute(
        text(
            "SELECT is_nullable FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = :t AND column_name = 'tenant_id'"
        ),
        {"t": table_name},
    ).fetchone()
    assert row is not None, f"{table_name} has no tenant_id column"
    assert row[0] == "NO", f"{table_name}.tenant_id must be NOT NULL"


def test_idg_reviews_extended_not_duplicated(db_session):
    for col in ("follow_up_required", "follow_up_status", "follow_up_completed_at"):
        row = db_session.execute(
            text(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_schema='public' AND table_name='idg_reviews' AND column_name=:c"
            ),
            {"c": col},
        ).fetchone()
        assert row is not None, f"idg_reviews.{col} missing"


def test_rnica_assessments_extended_no_second_status_column(db_session):
    row = db_session.execute(
        text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name='rnica_assessments' AND column_name='hope_submission_due_at'"
        )
    ).fetchone()
    assert row is not None

    dup = db_session.execute(
        text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name='rnica_assessments' "
            "AND column_name IN ('hope_status', 'hope_submission_status')"
        )
    ).fetchall()
    assert dup == []


# ---------------------------------------------------------------------
# Election-date resolution (Risks 1-3)
# ---------------------------------------------------------------------


def test_resolves_election_effective_date_from_benefit_period_only(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(
        db_session, patient, tenant_id, election_signed_at=datetime(2026, 10, 1, tzinfo=timezone.utc)
    )
    bp = _make_benefit_period(db_session, patient, tenant_id, election_date=date(2026, 10, 1))

    resolved = svc.resolve_election_effective_date_for_admission(db_session, admission.id)

    assert resolved.status == "RESOLVED"
    assert resolved.election_effective_date == date(2026, 10, 1)
    assert resolved.benefit_period_id == bp.id


def test_missing_benefit_period_election_date_requires_compliance_review(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id)
    # No benefit_period created at all for this patient.

    resolved = svc.resolve_election_effective_date_for_admission(db_session, admission.id)

    assert resolved.status == "COMPLIANCE_REVIEW_REQUIRED"
    assert resolved.validation_reason == svc.VALIDATION_REASON_MISSING_ELECTION_DATE
    assert resolved.election_effective_date is None


def test_election_date_earlier_than_signature_requires_compliance_review(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(
        db_session, patient, tenant_id, election_signed_at=datetime(2026, 10, 5, tzinfo=timezone.utc)
    )
    _make_benefit_period(db_session, patient, tenant_id, election_date=date(2026, 10, 1))

    resolved = svc.resolve_election_effective_date_for_admission(db_session, admission.id)

    assert resolved.status == "COMPLIANCE_REVIEW_REQUIRED"
    assert resolved.validation_reason == svc.VALIDATION_REASON_ELECTION_DATE_EARLIER_THAN_SIGNATURE


def test_admission_signed_at_never_used_as_deadline_source(db_session, tenant):
    """election_effective_date must equal benefit_periods.election_date even
    when admissions.election_signed_at differs (and is later, i.e. a valid
    condition) -- there is no fallback/blend between the two fields."""
    tenant_id = uuid.UUID(tenant.id)
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(
        db_session, patient, tenant_id, election_signed_at=datetime(2026, 9, 25, tzinfo=timezone.utc)
    )
    _make_benefit_period(db_session, patient, tenant_id, election_date=date(2026, 10, 1))

    resolved = svc.resolve_election_effective_date_for_admission(db_session, admission.id)

    assert resolved.status == "RESOLVED"
    assert resolved.election_effective_date == date(2026, 10, 1)
    assert resolved.election_effective_date != admission.election_signed_at.date()


# ---------------------------------------------------------------------
# Mandatory-rule boundary + idempotent creation
# ---------------------------------------------------------------------


def test_pre_rule_election_is_not_applicable(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(
        db_session, patient, tenant_id, election_signed_at=datetime(2026, 9, 1, tzinfo=timezone.utc)
    )
    _make_benefit_period(db_session, patient, tenant_id, election_date=date(2026, 9, 1))

    outcome = svc.get_or_create_mandatory_initial_addendum_requirement(
        db_session, tenant_id=tenant_id, admission_id=admission.id, created_by_user_id=TEST_USER_ID
    )

    assert outcome.outcome == "NOT_APPLICABLE"
    assert outcome.election_addendum_request is None


def test_mandatory_requirement_created_on_boundary_date(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(
        db_session, patient, tenant_id, election_signed_at=datetime(2026, 10, 1, tzinfo=timezone.utc)
    )
    bp = _make_benefit_period(db_session, patient, tenant_id, election_date=date(2026, 10, 1))

    outcome = svc.get_or_create_mandatory_initial_addendum_requirement(
        db_session, tenant_id=tenant_id, admission_id=admission.id, created_by_user_id=TEST_USER_ID
    )

    assert outcome.outcome == "CREATED"
    row = outcome.election_addendum_request
    assert row.trigger_type == "MANDATORY_INITIAL_ELECTION"
    assert row.mandatory_rule_applies is True
    assert row.benefit_period_id == bp.id
    assert row.election_effective_date == date(2026, 10, 1)
    assert row.required_by_at.date() == date(2026, 10, 6)  # +5 days


def test_mandatory_requirement_creation_is_idempotent(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(
        db_session, patient, tenant_id, election_signed_at=datetime(2026, 11, 1, tzinfo=timezone.utc)
    )
    _make_benefit_period(db_session, patient, tenant_id, election_date=date(2026, 11, 1))

    first = svc.get_or_create_mandatory_initial_addendum_requirement(
        db_session, tenant_id=tenant_id, admission_id=admission.id, created_by_user_id=TEST_USER_ID
    )
    second = svc.get_or_create_mandatory_initial_addendum_requirement(
        db_session, tenant_id=tenant_id, admission_id=admission.id, created_by_user_id=TEST_USER_ID
    )

    assert first.outcome == "CREATED"
    assert second.outcome == "EXISTING"
    assert second.election_addendum_request.id == first.election_addendum_request.id

    count = (
        db_session.query(ElectionAddendumRequest)
        .filter(
            ElectionAddendumRequest.admission_id == admission.id,
            ElectionAddendumRequest.trigger_type == "MANDATORY_INITIAL_ELECTION",
        )
        .count()
    )
    assert count == 1


def test_compliance_review_creates_no_addendum_row_and_is_idempotent(db_session, tenant):
    tenant_id = uuid.UUID(tenant.id)
    patient = _make_patient(db_session, tenant_id)
    admission = _make_admission(db_session, patient, tenant_id)
    # No benefit_period -> Risk 2 (missing election date).

    first = svc.get_or_create_mandatory_initial_addendum_requirement(
        db_session, tenant_id=tenant_id, admission_id=admission.id, created_by_user_id=TEST_USER_ID
    )
    second = svc.get_or_create_mandatory_initial_addendum_requirement(
        db_session, tenant_id=tenant_id, admission_id=admission.id, created_by_user_id=TEST_USER_ID
    )

    assert first.outcome == "COMPLIANCE_REVIEW_REQUIRED"
    assert first.election_addendum_request is None
    assert second.outcome == "COMPLIANCE_REVIEW_REQUIRED"
    assert second.compliance_obligation.id == first.compliance_obligation.id

    addendum_count = (
        db_session.query(ElectionAddendumRequest).filter(ElectionAddendumRequest.admission_id == admission.id).count()
    )
    assert addendum_count == 0

    obligation_count = (
        db_session.query(ComplianceObligation)
        .filter(
            ComplianceObligation.admission_id == admission.id,
            ComplianceObligation.obligation_type == "ELECTION_ADDENDUM_DATE_VALIDATION_REVIEW",
        )
        .count()
    )
    assert obligation_count == 1


def test_poc_change_uses_three_day_deadline():
    requirement = svc.compute_mandatory_addendum_requirement(
        election_effective_date=date(2026, 10, 1), poc_change_date=date(2026, 11, 10)
    )
    assert requirement.trigger_type == "PLAN_OF_CARE_CHANGE"
    assert requirement.required_by_date == date(2026, 11, 13)
