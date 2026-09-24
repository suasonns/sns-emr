"""Issue #157 remediation — automatic SFV completion "safety net" hook.

Product-authority rule (per Issue #157 decision — Option D with a
required clinician-facing ambiguity notice):

    The automatic finalize hook (`_maybe_complete_open_sfv_for_visit`)
    may NEVER select among multiple simultaneously-OPEN SFVRequirement
    rows using "oldest due", "earliest created", or any other
    patient-level inference. It may only auto-complete when there is
    EXACTLY ONE eligible OPEN requirement for the patient; with zero it
    must no-op, and with more than one it must leave every requirement
    OPEN and let the clinician resolve the ambiguity explicitly via the
    Symptom Follow-Up Visit section.

This suite verifies (repository-first gate) the actual remediation
implemented in `app.api.visits._maybe_complete_open_sfv_for_visit` and
its supporting `app.services.hope_phase_b_engine` helpers
(`get_eligible_open_sfv_requirements_for_visit`,
`find_visit_already_linked_sfv_requirement`), replacing the prior
`_find_oldest_open_sfv_requirement_for_patient` behavior that this test
suite's own docstrings previously flagged as unverified (see
test_sfv_completion_visit_separation.py's `TestSfvCompletionDefenseInDepth`
docstring).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.api.visits import _maybe_complete_open_sfv_for_visit
from app.models.admission import Admission
from app.models.audit_log import AuditLog
from app.models.patient import Patient
from app.models.sfv_requirement import SFVRequirement
from app.models.visit import Visit
from app.services.hope_phase_b_engine import (
    complete_sfv_requirement_from_visit,
    maybe_trigger_sfv_from_hope_timepoint,
    SFV_OUTCOME_AUTO_COMPLETED_SINGLE_MATCH,
    SFV_OUTCOME_DUPLICATE_COMPLETION_REJECTED,
    SFV_OUTCOME_SKIPPED_MULTIPLE_MATCHES,
    SFV_OUTCOME_SKIPPED_NO_MATCH,
)


def _make_patient_and_admission(db_session, tenant_id):
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"SFV-HOOK-{uuid.uuid4().hex[:12]}",
        date_of_birth=datetime(1940, 1, 1).date(),
        primary_diagnosis="Hospice qualifying diagnosis",
        status="ACTIVE",
        admission_status="PRE_REFERRAL",
        created_by=None,
    )
    db_session.add(patient)
    db_session.commit()

    admission = Admission(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient.id,
        status="ACTIVE",
    )
    db_session.add(admission)
    db_session.commit()

    return patient, admission


def _make_visit(
    db_session,
    tenant_id,
    patient,
    admission,
    provider_id,
    *,
    visit_type: str,
    visit_discipline: str,
    visit_datetime: datetime,
):
    visit = Visit(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient.id,
        admission_id=admission.id,
        provider_id=provider_id,
        visit_type=visit_type,
        visit_discipline=visit_discipline,
        visit_mode="IN_PERSON",
        status="COMPLETED",
        visit_datetime=visit_datetime,
    )
    db_session.add(visit)
    db_session.commit()
    return visit


def _trigger_requirement(
    db_session, tenant_id, patient, trigger_source_type, trigger_visit_id, trigger_datetime
):
    outcome = maybe_trigger_sfv_from_hope_timepoint(
        db=db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        trigger_source_type=trigger_source_type,
        trigger_reference_id=trigger_visit_id,
        trigger_datetime=trigger_datetime,
        pain_impact="SEVERE",
        non_pain_impact=None,
    )
    db_session.commit()
    assert outcome.created is True, outcome.reason
    return outcome


def _requirement(db_session, requirement_id):
    return (
        db_session.query(SFVRequirement)
        .filter(SFVRequirement.id == uuid.UUID(str(requirement_id)))
        .first()
    )


def _last_audit_outcome(db_session, patient_id):
    row = (
        db_session.query(AuditLog)
        .filter(AuditLog.action == "SFV_AUTO_COMPLETION_EVALUATED")
        .order_by(AuditLog.created_at.desc())
        .first()
    )
    assert row is not None, "expected an SFV_AUTO_COMPLETION_EVALUATED audit row"
    assert row.event_metadata["patientId"] == str(patient_id)
    return row.event_metadata["outcome"]


@pytest.fixture()
def rn_user_id():
    return uuid.UUID("11111111-1111-1111-1111-111111111111")


class TestAutomaticCompletionHookCandidateCounting:
    """AC-001 / AC-002 / AC-003."""

    def test_zero_open_requirements_no_mutation(self, db_session, tenant, rn_user_id):
        tenant_id = uuid.UUID(tenant.id)
        patient, admission = _make_patient_and_admission(db_session, tenant_id)
        now = datetime.now(timezone.utc)

        visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="SKILLED_NURSING", visit_discipline="RN", visit_datetime=now,
        )

        result = _maybe_complete_open_sfv_for_visit(db=db_session, visit=visit, request_id="test-req-1")
        db_session.commit()

        assert result is None
        assert _last_audit_outcome(db_session, patient.id) == SFV_OUTCOME_SKIPPED_NO_MATCH

    def test_exactly_one_open_requirement_auto_completes(self, db_session, tenant, rn_user_id):
        tenant_id = uuid.UUID(tenant.id)
        patient, admission = _make_patient_and_admission(db_session, tenant_id)
        now = datetime.now(timezone.utc)

        trigger_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
        )
        outcome = _trigger_requirement(
            db_session, tenant_id, patient, "INITIAL_RN_ICA", trigger_visit.id, now
        )

        completion_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="SKILLED_NURSING", visit_discipline="RN",
            visit_datetime=now + timedelta(hours=6),
        )

        result = _maybe_complete_open_sfv_for_visit(
            db=db_session, visit=completion_visit, request_id="test-req-2"
        )
        db_session.commit()

        assert result is not None
        assert str(result.id) == outcome.requirement_id
        assert result.status == "COMPLETED"
        assert result.completed_visit_id == completion_visit.id
        assert _last_audit_outcome(db_session, patient.id) == SFV_OUTCOME_AUTO_COMPLETED_SINGLE_MATCH

    def test_two_open_requirements_no_auto_completion(self, db_session, tenant, rn_user_id):
        """AC-003 / TEST-003 / TEST-004: two eligible OPEN requirements from
        different triggers (Admission + HUV1) must both remain OPEN --
        never resolved by oldest-due or any other inference."""
        tenant_id = uuid.UUID(tenant.id)
        patient, admission = _make_patient_and_admission(db_session, tenant_id)
        now = datetime.now(timezone.utc)

        admission_trigger_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
        )
        admission_outcome = _trigger_requirement(
            db_session, tenant_id, patient, "INITIAL_RN_ICA", admission_trigger_visit.id, now
        )

        huv1_trigger_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="HUV1", visit_discipline="RN",
            visit_datetime=now + timedelta(days=10),
        )
        huv1_outcome = _trigger_requirement(
            db_session, tenant_id, patient, "HUV1", huv1_trigger_visit.id,
            now + timedelta(days=10),
        )

        completion_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="SKILLED_NURSING", visit_discipline="RN",
            visit_datetime=now + timedelta(days=14),
        )

        result = _maybe_complete_open_sfv_for_visit(
            db=db_session, visit=completion_visit, request_id="test-req-3"
        )
        db_session.commit()

        assert result is None
        admission_requirement = _requirement(db_session, admission_outcome.requirement_id)
        huv1_requirement = _requirement(db_session, huv1_outcome.requirement_id)
        assert admission_requirement.status == "OPEN"
        assert admission_requirement.completed_visit_id is None
        assert huv1_requirement.status == "OPEN"
        assert huv1_requirement.completed_visit_id is None
        assert _last_audit_outcome(db_session, patient.id) == SFV_OUTCOME_SKIPPED_MULTIPLE_MATCHES


class TestAutomaticCompletionHookIdempotencyAndTriggerIsolation:
    """AC-004 / AC-006 / AC-007."""

    def test_explicit_selection_with_two_open_requirements(self, db_session, tenant, rn_user_id):
        """AC-004: with two OPEN requirements, an explicit completion of one
        (via complete_sfv_requirement_from_visit, the same command the
        interactive UI calls) leaves the other untouched and preserves its
        own trigger identity."""
        tenant_id = uuid.UUID(tenant.id)
        patient, admission = _make_patient_and_admission(db_session, tenant_id)
        now = datetime.now(timezone.utc)

        admission_trigger_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
        )
        admission_outcome = _trigger_requirement(
            db_session, tenant_id, patient, "INITIAL_RN_ICA", admission_trigger_visit.id, now
        )

        huv1_trigger_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="HUV1", visit_discipline="RN",
            visit_datetime=now + timedelta(days=10),
        )
        huv1_outcome = _trigger_requirement(
            db_session, tenant_id, patient, "HUV1", huv1_trigger_visit.id,
            now + timedelta(days=10),
        )

        completion_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="SKILLED_NURSING", visit_discipline="RN",
            visit_datetime=now + timedelta(days=14),
        )

        # Clinician explicitly selects and completes the HUV1-linked
        # requirement (mirrors the SymptomFollowUpVisitSection UI).
        completed = complete_sfv_requirement_from_visit(
            db=db_session,
            sfv_requirement_id=huv1_outcome.requirement_id,
            completing_visit_id=completion_visit.id,
            completing_visit_datetime=completion_visit.visit_datetime,
            discipline="RN",
            visit_mode="IN_PERSON",
        )
        db_session.commit()

        assert completed.status == "COMPLETED"
        assert str(completed.id) == huv1_outcome.requirement_id
        assert completed.trigger_source_type == "HUV1"

        admission_requirement = _requirement(db_session, admission_outcome.requirement_id)
        assert admission_requirement.status == "OPEN"
        assert admission_requirement.completed_visit_id is None

    def test_admission_and_huv2_open_selecting_huv2_only_changes_huv2(
        self, db_session, tenant, rn_user_id
    ):
        """Same guarantee as the Admission+HUV1 case, for the HUV2 timepoint."""
        tenant_id = uuid.UUID(tenant.id)
        patient, admission = _make_patient_and_admission(db_session, tenant_id)
        now = datetime.now(timezone.utc)

        admission_trigger_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
        )
        admission_outcome = _trigger_requirement(
            db_session, tenant_id, patient, "INITIAL_RN_ICA", admission_trigger_visit.id, now
        )

        huv2_trigger_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="HUV2", visit_discipline="RN",
            visit_datetime=now + timedelta(days=20),
        )
        huv2_outcome = _trigger_requirement(
            db_session, tenant_id, patient, "HUV2", huv2_trigger_visit.id,
            now + timedelta(days=20),
        )

        completion_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="SKILLED_NURSING", visit_discipline="RN",
            visit_datetime=now + timedelta(days=22),
        )

        completed = complete_sfv_requirement_from_visit(
            db=db_session,
            sfv_requirement_id=huv2_outcome.requirement_id,
            completing_visit_id=completion_visit.id,
            completing_visit_datetime=completion_visit.visit_datetime,
            discipline="RN",
            visit_mode="IN_PERSON",
        )
        db_session.commit()

        assert completed.status == "COMPLETED"
        assert str(completed.id) == huv2_outcome.requirement_id
        assert completed.trigger_source_type == "HUV2"

        admission_requirement = _requirement(db_session, admission_outcome.requirement_id)
        assert admission_requirement.status == "OPEN"
        assert admission_requirement.completed_visit_id is None

    def test_explicit_completion_rejects_visit_already_linked_elsewhere(
        self, db_session, tenant, rn_user_id
    ):
        """Backend safeguard (final Issue #157 decision): a visit that has
        already completed one SFVRequirement must be REJECTED -- not
        silently accepted -- if re-targeted at a second, different
        requirement via the explicit completion command."""
        tenant_id = uuid.UUID(tenant.id)
        patient, admission = _make_patient_and_admission(db_session, tenant_id)
        now = datetime.now(timezone.utc)

        admission_trigger_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
        )
        admission_outcome = _trigger_requirement(
            db_session, tenant_id, patient, "INITIAL_RN_ICA", admission_trigger_visit.id, now
        )

        huv1_trigger_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="HUV1", visit_discipline="RN",
            visit_datetime=now + timedelta(days=10),
        )
        huv1_outcome = _trigger_requirement(
            db_session, tenant_id, patient, "HUV1", huv1_trigger_visit.id,
            now + timedelta(days=10),
        )

        completion_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="SKILLED_NURSING", visit_discipline="RN",
            visit_datetime=now + timedelta(days=14),
        )

        complete_sfv_requirement_from_visit(
            db=db_session,
            sfv_requirement_id=admission_outcome.requirement_id,
            completing_visit_id=completion_visit.id,
            completing_visit_datetime=completion_visit.visit_datetime,
            discipline="RN",
            visit_mode="IN_PERSON",
        )
        db_session.commit()

        with pytest.raises(ValueError, match="already used to complete a different SFV requirement"):
            complete_sfv_requirement_from_visit(
                db=db_session,
                sfv_requirement_id=huv1_outcome.requirement_id,
                completing_visit_id=completion_visit.id,
                completing_visit_datetime=completion_visit.visit_datetime,
                discipline="RN",
                visit_mode="IN_PERSON",
            )
        db_session.rollback()

        huv1_requirement = _requirement(db_session, huv1_outcome.requirement_id)
        assert huv1_requirement.status == "OPEN"
        assert huv1_requirement.completed_visit_id is None

    def test_same_visit_cannot_complete_two_requirements(self, db_session, tenant, rn_user_id):
        """AC-006: once Visit X has explicitly completed Requirement B, the
        automatic hook running for that same visit must NOT also complete
        Requirement A -- the exact silent-misattribution defect Issue #157
        identified."""
        tenant_id = uuid.UUID(tenant.id)
        patient, admission = _make_patient_and_admission(db_session, tenant_id)
        now = datetime.now(timezone.utc)

        admission_trigger_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
        )
        admission_outcome = _trigger_requirement(
            db_session, tenant_id, patient, "INITIAL_RN_ICA", admission_trigger_visit.id, now
        )

        huv1_trigger_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="HUV1", visit_discipline="RN",
            visit_datetime=now + timedelta(days=10),
        )
        huv1_outcome = _trigger_requirement(
            db_session, tenant_id, patient, "HUV1", huv1_trigger_visit.id,
            now + timedelta(days=10),
        )

        completion_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="SKILLED_NURSING", visit_discipline="RN",
            visit_datetime=now + timedelta(days=14),
        )

        # Explicit completion of Requirement B (HUV1-linked) by Visit X.
        complete_sfv_requirement_from_visit(
            db=db_session,
            sfv_requirement_id=huv1_outcome.requirement_id,
            completing_visit_id=completion_visit.id,
            completing_visit_datetime=completion_visit.visit_datetime,
            discipline="RN",
            visit_mode="IN_PERSON",
        )
        db_session.commit()

        # Visit X's finalization now invokes the automatic hook (e.g. an
        # addendum/re-finalize). It must be a no-op, not a second
        # completion of the still-OPEN Admission-linked requirement.
        result = _maybe_complete_open_sfv_for_visit(
            db=db_session, visit=completion_visit, request_id="test-req-4"
        )
        db_session.commit()

        assert result is None
        admission_requirement = _requirement(db_session, admission_outcome.requirement_id)
        assert admission_requirement.status == "OPEN"
        assert admission_requirement.completed_visit_id is None
        assert _last_audit_outcome(db_session, patient.id) == SFV_OUTCOME_DUPLICATE_COMPLETION_REJECTED

    def test_trigger_isolation_huv1_completion_does_not_touch_admission(
        self, db_session, tenant, rn_user_id
    ):
        """AC-007: completing the HUV1-triggered requirement (whether
        explicitly or, here, via the automatic hook when it is the sole
        eligible candidate) never changes the Admission-triggered
        requirement, and vice versa."""
        tenant_id = uuid.UUID(tenant.id)
        patient, admission = _make_patient_and_admission(db_session, tenant_id)
        now = datetime.now(timezone.utc)

        admission_trigger_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
        )
        admission_outcome = _trigger_requirement(
            db_session, tenant_id, patient, "INITIAL_RN_ICA", admission_trigger_visit.id, now
        )

        # Admission-linked requirement completed first (only one OPEN at
        # the time), before the HUV1 trigger exists.
        first_completion_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="SKILLED_NURSING", visit_discipline="RN",
            visit_datetime=now + timedelta(hours=6),
        )
        result = _maybe_complete_open_sfv_for_visit(
            db=db_session, visit=first_completion_visit, request_id="test-req-5"
        )
        db_session.commit()
        assert result is not None
        assert str(result.id) == admission_outcome.requirement_id

        huv1_trigger_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="HUV1", visit_discipline="RN",
            visit_datetime=now + timedelta(days=10),
        )
        huv1_outcome = _trigger_requirement(
            db_session, tenant_id, patient, "HUV1", huv1_trigger_visit.id,
            now + timedelta(days=10),
        )

        second_completion_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="SKILLED_NURSING", visit_discipline="RN",
            visit_datetime=now + timedelta(days=12),
        )
        result2 = _maybe_complete_open_sfv_for_visit(
            db=db_session, visit=second_completion_visit, request_id="test-req-6"
        )
        db_session.commit()

        assert result2 is not None
        assert str(result2.id) == huv1_outcome.requirement_id

        admission_requirement = _requirement(db_session, admission_outcome.requirement_id)
        assert admission_requirement.status == "COMPLETED"
        assert admission_requirement.completed_visit_id == first_completion_visit.id
