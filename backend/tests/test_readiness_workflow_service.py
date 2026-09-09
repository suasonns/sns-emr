"""
Tests for app.billing.services.readiness_workflow_service (Sprint 2 --
Billing Readiness Operational Workflow, Phase 1): readiness status
derivation, typed blocker taxonomy, blocker lifecycle sync, and the
generic assignment/follow-up framework with its shared audit trail.

Runs against the real test Postgres DB (db_session fixture), reusing the
fixture helpers already established in test_billing_readiness_service.py
(same cross-test-module import pattern used by
test_billing_readiness_verdict_persistence.py).
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest

from app.billing.models.billing_blocker_record import (
    SYSTEM_AUTO_RESOLVED_BY,
    BillingBlockerRecord,
)
from app.billing.models.readiness_assignment import ReadinessAssignment
from app.billing.models.readiness_follow_up import ReadinessFollowUp
from app.billing.models.readiness_workflow_event import ReadinessWorkflowEvent
from app.billing.services.billing_readiness_service import (
    check_patient_billing_readiness,
)
from app.billing.services.readiness_workflow_service import (
    classify_blocker_code,
    compute_operational_bucket,
    derive_readiness_status,
    resolve_blocker_manually,
    upsert_assignment,
    upsert_follow_up,
)
from tests.conftest import TEST_USER_ID
from tests.test_billing_readiness_service import (
    SERVICE_DATE,
    _make_approved_poc,
    _make_benefit_period,
    _make_certification,
    _make_patient,
    _make_payer,
)


@pytest.fixture(autouse=True)
def _clean_patient_payers_leftovers(db_session, tenant):
    """Same leftover-payer guard as test_billing_readiness_service.py --
    patient_payers has no tenant_id column so the generic cleanup sweep
    can't reach it."""
    from sqlalchemy import text as _text

    db_session.execute(
        _text(
            "DELETE FROM patient_payers WHERE patient_id IN "
            "(SELECT id FROM patients WHERE tenant_id = :tenant_id)"
        ),
        {"tenant_id": uuid.UUID(tenant.id)},
    )
    db_session.commit()
    yield


# ---------------------------------------------------------------------
# Deliverable 2 -- readiness status derivation (pure)
# ---------------------------------------------------------------------

class TestDeriveReadinessStatus:
    def test_not_ready_when_blockers_present(self):
        assert derive_readiness_status(blockers=["x"], warnings=[]) == "NOT_READY"

    def test_not_ready_wins_over_warnings(self):
        assert derive_readiness_status(blockers=["x"], warnings=["y"]) == "NOT_READY"

    def test_at_risk_when_only_warnings(self):
        assert derive_readiness_status(blockers=[], warnings=["y"]) == "AT_RISK"

    def test_ready_when_neither(self):
        assert derive_readiness_status(blockers=[], warnings=[]) == "READY"


class TestComputeOperationalBucket:
    def test_not_ready_without_blocked_follow_up_stays_not_ready(self):
        assert (
            compute_operational_bucket(
                readiness_status="NOT_READY", has_open_blocked_follow_up=False
            )
            == "NOT_READY"
        )

    def test_not_ready_with_blocked_follow_up_becomes_blocked(self):
        assert (
            compute_operational_bucket(
                readiness_status="NOT_READY", has_open_blocked_follow_up=True
            )
            == "BLOCKED"
        )

    def test_ready_never_reclassified_as_blocked(self):
        assert (
            compute_operational_bucket(
                readiness_status="READY", has_open_blocked_follow_up=True
            )
            == "READY"
        )

    def test_at_risk_never_reclassified_as_blocked(self):
        assert (
            compute_operational_bucket(
                readiness_status="AT_RISK", has_open_blocked_follow_up=True
            )
            == "AT_RISK"
        )


# ---------------------------------------------------------------------
# Deliverable 3 -- typed blocker taxonomy mapping
# ---------------------------------------------------------------------

class TestClassifyBlockerCode:
    @pytest.mark.parametrize(
        "message,expected_code",
        [
            ("Patient status is 'DISCHARGED', not ACTIVE.", "OTHER"),
            ("No benefit period covers the service date 2026-03-15.", "BENEFIT_PERIOD_ISSUE"),
            ("Hospice election statement is not signed.", "MISSING_DOCUMENTATION"),
            (
                "Notice of Election (NOE) has not been filed and no CMS exception is documented -- Medicare will return the claim.",
                "BENEFIT_PERIOD_ISSUE",
            ),
            (
                "Certification of Terminal Illness (CTI/Recert) is not signed and finalized for this benefit period.",
                "MISSING_CERTIFICATION",
            ),
            (
                "Required face-to-face encounter is not attested for this benefit period.",
                "MISSING_FACE_TO_FACE",
            ),
            (
                "Plan of Care is not active with a physician signature on file.",
                "MISSING_PHYSICIAN_SIGNATURE",
            ),
            ("Payer sequence is ambiguous: conflicting priority.", "OTHER"),
            ("Patient not found for this tenant.", "OTHER"),
        ],
    )
    def test_known_prefixes_map_to_expected_code(self, message, expected_code):
        assert classify_blocker_code(message) == expected_code

    def test_unknown_blocker_falls_back_to_other(self):
        assert classify_blocker_code("Some brand new blocker nobody mapped yet.") == "OTHER"


# ---------------------------------------------------------------------
# Blocker lifecycle sync (integration, via check_patient_billing_readiness)
# ---------------------------------------------------------------------

def _blocker_records_for(db_session, patient_id):
    return (
        db_session.query(BillingBlockerRecord)
        .filter(BillingBlockerRecord.patient_id == patient_id)
        .all()
    )


class TestBlockerRecordLifecycle:
    def test_new_blocker_opens_a_typed_record(self, db_session, tenant):
        patient = _make_patient(db_session, tenant.id, mrn="MRN-BLOCKER-OPEN")
        # No benefit period at all -> guaranteed BENEFIT_PERIOD_ISSUE blocker.

        result = check_patient_billing_readiness(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            service_date=SERVICE_DATE,
        )
        assert result.ready is False

        records = _blocker_records_for(db_session, patient.id)
        assert len(records) == 1
        assert records[0].status == "OPEN"
        assert records[0].blocker_code == "BENEFIT_PERIOD_ISSUE"
        assert records[0].message == result.blockers[0]

    def test_repeated_evaluation_does_not_duplicate_open_blocker(self, db_session, tenant):
        patient = _make_patient(db_session, tenant.id, mrn="MRN-BLOCKER-REPEAT")

        check_patient_billing_readiness(
            db_session, tenant_id=tenant.id, patient_id=str(patient.id), service_date=SERVICE_DATE,
        )
        first_pass = _blocker_records_for(db_session, patient.id)
        assert len(first_pass) == 1
        first_last_seen_verdict_id = first_pass[0].last_seen_verdict_id

        check_patient_billing_readiness(
            db_session, tenant_id=tenant.id, patient_id=str(patient.id), service_date=SERVICE_DATE,
        )
        second_pass = _blocker_records_for(db_session, patient.id)
        assert len(second_pass) == 1
        assert second_pass[0].status == "OPEN"
        assert second_pass[0].last_seen_verdict_id != first_last_seen_verdict_id

    def test_blocker_auto_resolves_once_patient_becomes_ready(self, db_session, tenant):
        patient = _make_patient(db_session, tenant.id, mrn="MRN-BLOCKER-AUTORESOLVE")

        check_patient_billing_readiness(
            db_session, tenant_id=tenant.id, patient_id=str(patient.id), service_date=SERVICE_DATE,
        )
        assert _blocker_records_for(db_session, patient.id)[0].status == "OPEN"

        bp = _make_benefit_period(db_session, tenant.id, patient)
        _make_certification(db_session, tenant.id, patient, bp)
        _make_approved_poc(db_session, tenant.id, patient)
        _make_payer(db_session, patient)

        result = check_patient_billing_readiness(
            db_session, tenant_id=tenant.id, patient_id=str(patient.id), service_date=SERVICE_DATE,
        )
        assert result.ready is True

        records = _blocker_records_for(db_session, patient.id)
        assert len(records) == 1
        assert records[0].status == "RESOLVED"
        assert records[0].resolved_by == SYSTEM_AUTO_RESOLVED_BY

    def test_manual_resolution_records_workflow_event(self, db_session, tenant):
        patient = _make_patient(db_session, tenant.id, mrn="MRN-BLOCKER-MANUAL")
        check_patient_billing_readiness(
            db_session, tenant_id=tenant.id, patient_id=str(patient.id), service_date=SERVICE_DATE,
        )
        record = _blocker_records_for(db_session, patient.id)[0]

        resolved = resolve_blocker_manually(
            db_session,
            blocker_id=str(record.id),
            actor_user_id=str(TEST_USER_ID),
            reason="Confirmed benefit period backdated in source system.",
        )
        assert resolved.status == "RESOLVED"
        assert resolved.resolved_by == str(TEST_USER_ID)

        events = (
            db_session.query(ReadinessWorkflowEvent)
            .filter(
                ReadinessWorkflowEvent.entity_type == "BLOCKER",
                ReadinessWorkflowEvent.entity_id == record.id,
            )
            .all()
        )
        assert len(events) == 1
        assert events[0].event_type == "RESOLVED"
        assert events[0].actor_user_id == TEST_USER_ID
        assert events[0].reason == "Confirmed benefit period backdated in source system."


# ---------------------------------------------------------------------
# Deliverable 4 -- generic assignment framework
# ---------------------------------------------------------------------

class TestUpsertAssignment:
    def test_creates_assignment_and_audit_event(self, db_session, tenant):
        patient = _make_patient(db_session, tenant.id, mrn="MRN-ASSIGN-CREATE")

        assignment = upsert_assignment(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            actor_user_id=str(TEST_USER_ID),
            assigned_user_id=str(TEST_USER_ID),
            assigned_role="Reviewer",
            assignment_status="ASSIGNED",
        )

        assert assignment.assignment_status == "ASSIGNED"
        assert assignment.assigned_role == "Reviewer"

        events = (
            db_session.query(ReadinessWorkflowEvent)
            .filter(
                ReadinessWorkflowEvent.entity_type == "ASSIGNMENT",
                ReadinessWorkflowEvent.entity_id == assignment.id,
            )
            .all()
        )
        assert len(events) == 1
        assert events[0].event_type == "CREATED"
        assert events[0].previous_value is None
        assert events[0].new_value["assignment_status"] == "ASSIGNED"

    def test_updating_existing_assignment_writes_second_event(self, db_session, tenant):
        patient = _make_patient(db_session, tenant.id, mrn="MRN-ASSIGN-UPDATE")

        assignment = upsert_assignment(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            actor_user_id=str(TEST_USER_ID),
            assigned_user_id=str(TEST_USER_ID),
            assignment_status="ASSIGNED",
        )

        upsert_assignment(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            actor_user_id=str(TEST_USER_ID),
            assigned_user_id=str(TEST_USER_ID),
            assignment_status="COMPLETED",
        )

        assert (
            db_session.query(ReadinessAssignment)
            .filter(ReadinessAssignment.id == assignment.id)
            .one()
            .assignment_status
            == "COMPLETED"
        )

        events = (
            db_session.query(ReadinessWorkflowEvent)
            .filter(
                ReadinessWorkflowEvent.entity_type == "ASSIGNMENT",
                ReadinessWorkflowEvent.entity_id == assignment.id,
            )
            .all()
        )
        assert len(events) == 2

    def test_rejects_invalid_assignment_status(self, db_session, tenant):
        patient = _make_patient(db_session, tenant.id, mrn="MRN-ASSIGN-INVALID")
        with pytest.raises(ValueError):
            upsert_assignment(
                db_session,
                tenant_id=tenant.id,
                patient_id=str(patient.id),
                actor_user_id=str(TEST_USER_ID),
                assignment_status="NOT_A_REAL_STATUS",
            )


# ---------------------------------------------------------------------
# Deliverable 5 -- follow-up tracking
# ---------------------------------------------------------------------

class TestUpsertFollowUp:
    def test_creates_follow_up_and_audit_event(self, db_session, tenant):
        patient = _make_patient(db_session, tenant.id, mrn="MRN-FOLLOWUP-CREATE")

        follow_up = upsert_follow_up(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            actor_user_id=str(TEST_USER_ID),
            status="OPEN",
            due_date=date.today() + timedelta(days=3),
            notes="Waiting on physician signature.",
        )

        assert follow_up.status == "OPEN"
        assert follow_up.follow_up_required is True

        events = (
            db_session.query(ReadinessWorkflowEvent)
            .filter(
                ReadinessWorkflowEvent.entity_type == "FOLLOW_UP",
                ReadinessWorkflowEvent.entity_id == follow_up.id,
            )
            .all()
        )
        assert len(events) == 1
        assert events[0].event_type == "CREATED"

    def test_marking_blocked_is_audited_and_sets_status(self, db_session, tenant):
        patient = _make_patient(db_session, tenant.id, mrn="MRN-FOLLOWUP-BLOCKED")

        follow_up = upsert_follow_up(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            actor_user_id=str(TEST_USER_ID),
            status="OPEN",
        )

        updated = upsert_follow_up(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            actor_user_id=str(TEST_USER_ID),
            follow_up_id=str(follow_up.id),
            status="BLOCKED",
            reason="Waiting on external physician office to return signed CTI.",
        )

        assert updated.status == "BLOCKED"

        events = (
            db_session.query(ReadinessWorkflowEvent)
            .filter(
                ReadinessWorkflowEvent.entity_type == "FOLLOW_UP",
                ReadinessWorkflowEvent.entity_id == follow_up.id,
            )
            .order_by(ReadinessWorkflowEvent.occurred_at.asc())
            .all()
        )
        assert len(events) == 2
        assert events[-1].event_type == "STATUS_CHANGED"
        assert events[-1].new_value["status"] == "BLOCKED"
        assert events[-1].reason == "Waiting on external physician office to return signed CTI."

    def test_resolving_sets_resolved_date(self, db_session, tenant):
        patient = _make_patient(db_session, tenant.id, mrn="MRN-FOLLOWUP-RESOLVE")

        follow_up = upsert_follow_up(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            actor_user_id=str(TEST_USER_ID),
            status="OPEN",
        )

        resolved = upsert_follow_up(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            actor_user_id=str(TEST_USER_ID),
            follow_up_id=str(follow_up.id),
            status="RESOLVED",
        )

        assert resolved.status == "RESOLVED"
        assert resolved.resolved_date == date.today()

    def test_rejects_invalid_status(self, db_session, tenant):
        patient = _make_patient(db_session, tenant.id, mrn="MRN-FOLLOWUP-INVALID")
        with pytest.raises(ValueError):
            upsert_follow_up(
                db_session,
                tenant_id=tenant.id,
                patient_id=str(patient.id),
                actor_user_id=str(TEST_USER_ID),
                status="NOT_A_REAL_STATUS",
            )
