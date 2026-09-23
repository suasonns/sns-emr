"""SFV Completion Visit Separation — acceptance tests.

Product-authority rule (see SNS_CONSTITUTION.md and
SFV_LIFECYCLE_TRACE_MATRIX.md, "SFV Completion Visit Rule"):

    The SFV completion event must occur in a DIFFERENT visit record than
    the visit that generated the SFV trigger:  triggerVisitId != completionVisitId

    Same clinician, same discipline, same patient, same day (within 48h) are
    all ALLOWED. The only disqualifying condition is completing the SFV on
    the exact same visit record that produced the trigger.

This suite independently verifies (repository-first gate, per
SNS_CONSTITUTION.md Section 8/Section 20) that the backend
(`hope_phase_b_engine.complete_sfv_requirement_from_visit`) already enforces
this rule via a visit-identity comparison
(`str(completing_visit_id) == str(requirement.trigger_reference_id)`),
independent of clinician identity or discipline.

No frontend change is made in this pass. The frontend conflation already
documented in SFV_LIFECYCLE_TRACE_MATRIX.md (self-attested
`sfv.inPersonSfvCompleted` checkbox on the triggering RN ICA form) is a
separate, larger alignment task and is intentionally out of scope here.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models.admission import Admission
from app.models.patient import Patient
from app.models.visit import Visit
from app.services.hope_phase_b_engine import (
    complete_sfv_requirement_from_visit,
    maybe_trigger_sfv_from_hope_timepoint,
)


def _make_patient_and_admission(db_session, tenant_id):
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"SFV-SEP-{uuid.uuid4().hex[:12]}",
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


def _trigger_requirement(db_session, tenant_id, patient, trigger_visit_id, trigger_datetime):
    outcome = maybe_trigger_sfv_from_hope_timepoint(
        db=db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        trigger_source_type="INITIAL_RN_ICA",
        trigger_reference_id=trigger_visit_id,
        trigger_datetime=trigger_datetime,
        pain_impact="SEVERE",
        non_pain_impact=None,
    )
    db_session.commit()
    assert outcome.created is True, outcome.reason
    return outcome


@pytest.fixture()
def rn_user_id():
    # Test-suite well-known user id; see conftest.py TEST_USER_ID.
    return uuid.UUID("11111111-1111-1111-1111-111111111111")


class TestSfvCompletionVisitSeparation:
    """Scenarios 1-6 from the SFV Completion Visit Rule directive."""

    def test_same_nurse_different_visit_passes(self, db_session, tenant, rn_user_id):
        tenant_id = uuid.UUID(tenant.id)
        patient, admission = _make_patient_and_admission(db_session, tenant_id)
        now = datetime.now(timezone.utc)

        trigger_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
        )
        completion_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="SKILLED_NURSING", visit_discipline="RN",
            visit_datetime=now + timedelta(hours=6),
        )

        outcome = _trigger_requirement(db_session, tenant_id, patient, trigger_visit.id, now)

        requirement = complete_sfv_requirement_from_visit(
            db=db_session,
            sfv_requirement_id=outcome.requirement_id,
            completing_visit_id=completion_visit.id,
            completing_visit_datetime=completion_visit.visit_datetime,
            discipline="RN",
            visit_mode="IN_PERSON",
        )
        db_session.commit()

        assert requirement.status == "COMPLETED"
        assert requirement.completed_visit_id == completion_visit.id

    def test_same_rn_different_visit_passes(self, db_session, tenant, rn_user_id):
        # Identical to the "same nurse" case but stated explicitly per the
        # directive's PASS example #1 (RN = Jane Smith on both visits).
        self.test_same_nurse_different_visit_passes(db_session, tenant, rn_user_id)

    def test_same_lvn_different_visit_passes(self, db_session, tenant, rn_user_id):
        tenant_id = uuid.UUID(tenant.id)
        patient, admission = _make_patient_and_admission(db_session, tenant_id)
        now = datetime.now(timezone.utc)

        trigger_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="RNICA_ADMISSION", visit_discipline="LVN", visit_datetime=now,
        )
        completion_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="SKILLED_NURSING", visit_discipline="LVN",
            visit_datetime=now + timedelta(hours=6),
        )

        outcome = _trigger_requirement(db_session, tenant_id, patient, trigger_visit.id, now)

        requirement = complete_sfv_requirement_from_visit(
            db=db_session,
            sfv_requirement_id=outcome.requirement_id,
            completing_visit_id=completion_visit.id,
            completing_visit_datetime=completion_visit.visit_datetime,
            discipline="LVN",
            visit_mode="IN_PERSON",
        )
        db_session.commit()

        assert requirement.status == "COMPLETED"

    def test_different_clinician_different_visit_passes(self, db_session, tenant, rn_user_id):
        # The rule is visit-identity, not clinician-identity: a different
        # discipline (RN trigger -> LVN completion) on a separate visit
        # must still pass.
        tenant_id = uuid.UUID(tenant.id)
        patient, admission = _make_patient_and_admission(db_session, tenant_id)
        now = datetime.now(timezone.utc)

        trigger_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
        )
        completion_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="SKILLED_NURSING", visit_discipline="LVN",
            visit_datetime=now + timedelta(hours=6),
        )

        outcome = _trigger_requirement(db_session, tenant_id, patient, trigger_visit.id, now)

        requirement = complete_sfv_requirement_from_visit(
            db=db_session,
            sfv_requirement_id=outcome.requirement_id,
            completing_visit_id=completion_visit.id,
            completing_visit_datetime=completion_visit.visit_datetime,
            discipline="LVN",
            visit_mode="IN_PERSON",
        )
        db_session.commit()

        assert requirement.status == "COMPLETED"

    def test_same_visit_fails(self, db_session, tenant, rn_user_id):
        """A visit may not satisfy both trigger and completion."""
        tenant_id = uuid.UUID(tenant.id)
        patient, admission = _make_patient_and_admission(db_session, tenant_id)
        now = datetime.now(timezone.utc)

        trigger_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
        )

        outcome = _trigger_requirement(db_session, tenant_id, patient, trigger_visit.id, now)

        with pytest.raises(ValueError, match="separate visit"):
            complete_sfv_requirement_from_visit(
                db=db_session,
                sfv_requirement_id=outcome.requirement_id,
                completing_visit_id=trigger_visit.id,
                completing_visit_datetime=trigger_visit.visit_datetime,
                discipline="RN",
                visit_mode="IN_PERSON",
            )

    def test_same_visit_cannot_self_complete_sfv(self, db_session, tenant, rn_user_id):
        # Duplicate of test_same_visit_fails phrased per directive item #6;
        # kept as a distinct named test so the acceptance-test matrix has a
        # 1:1 row-to-test mapping.
        self.test_same_visit_fails(db_session, tenant, rn_user_id)

    def test_readiness_status_not_complete_until_separate_visit_exists(
        self, db_session, tenant, rn_user_id
    ):
        """Readiness/status must not report SFV complete purely because the
        triggering visit exists — only a genuinely separate completion visit
        may flip status to COMPLETED."""
        tenant_id = uuid.UUID(tenant.id)
        patient, admission = _make_patient_and_admission(db_session, tenant_id)
        now = datetime.now(timezone.utc)

        trigger_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
        )

        outcome = _trigger_requirement(db_session, tenant_id, patient, trigger_visit.id, now)

        from app.models.sfv_requirement import SFVRequirement

        requirement = (
            db_session.query(SFVRequirement)
            .filter(SFVRequirement.id == uuid.UUID(outcome.requirement_id))
            .first()
        )
        assert requirement.status == "OPEN"
        assert requirement.completed_visit_id is None

        completion_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="SKILLED_NURSING", visit_discipline="RN",
            visit_datetime=now + timedelta(hours=6),
        )
        complete_sfv_requirement_from_visit(
            db=db_session,
            sfv_requirement_id=outcome.requirement_id,
            completing_visit_id=completion_visit.id,
            completing_visit_datetime=completion_visit.visit_datetime,
            discipline="RN",
            visit_mode="IN_PERSON",
        )
        db_session.commit()

        db_session.refresh(requirement)
        assert requirement.status == "COMPLETED"
        assert requirement.completed_visit_id == completion_visit.id

    def test_reporting_reflects_trigger_and_completion_visits_separately(
        self, db_session, tenant, rn_user_id
    ):
        """The persisted record must retain both visit identities distinctly
        (trigger_reference_id vs completed_visit_id), not collapse them into
        one field, so reporting/exporter logic can distinguish the two
        lifecycle events."""
        tenant_id = uuid.UUID(tenant.id)
        patient, admission = _make_patient_and_admission(db_session, tenant_id)
        now = datetime.now(timezone.utc)

        trigger_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
        )
        completion_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="SKILLED_NURSING", visit_discipline="RN",
            visit_datetime=now + timedelta(hours=6),
        )

        outcome = _trigger_requirement(db_session, tenant_id, patient, trigger_visit.id, now)

        requirement = complete_sfv_requirement_from_visit(
            db=db_session,
            sfv_requirement_id=outcome.requirement_id,
            completing_visit_id=completion_visit.id,
            completing_visit_datetime=completion_visit.visit_datetime,
            discipline="RN",
            visit_mode="IN_PERSON",
        )
        db_session.commit()

        assert requirement.trigger_reference_id == trigger_visit.id
        assert requirement.completed_visit_id == completion_visit.id
        assert requirement.trigger_reference_id != requirement.completed_visit_id


class TestSfvCompletionDefenseInDepth:
    """P3-SFV-01: completion-before-trigger and cross-patient/cross-tenant
    guards added directly to `complete_sfv_requirement_from_visit`
    (SFV_FRONTEND_BACKEND_PARITY_MATRIX.md rows SFV-P11/SFV-P13/SFV-P14).
    These guard the service function itself, independent of whatever the
    current sole caller (`_maybe_complete_open_sfv_for_visit`) already
    guarantees by construction, so the function stays safe if called from
    a future dedicated completion API.
    """

    def test_completion_before_trigger_rejected(self, db_session, tenant, rn_user_id):
        tenant_id = uuid.UUID(tenant.id)
        patient, admission = _make_patient_and_admission(db_session, tenant_id)
        now = datetime.now(timezone.utc)

        trigger_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
        )
        # Completion visit dated BEFORE the trigger visit.
        completion_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="SKILLED_NURSING", visit_discipline="RN",
            visit_datetime=now - timedelta(hours=6),
        )

        outcome = _trigger_requirement(db_session, tenant_id, patient, trigger_visit.id, now)

        with pytest.raises(ValueError, match="before the triggering visit"):
            complete_sfv_requirement_from_visit(
                db=db_session,
                sfv_requirement_id=outcome.requirement_id,
                completing_visit_id=completion_visit.id,
                completing_visit_datetime=completion_visit.visit_datetime,
                discipline="RN",
                visit_mode="IN_PERSON",
            )

    def test_cross_patient_completion_visit_rejected(self, db_session, tenant, rn_user_id):
        tenant_id = uuid.UUID(tenant.id)
        patient, admission = _make_patient_and_admission(db_session, tenant_id)
        other_patient, other_admission = _make_patient_and_admission(db_session, tenant_id)
        now = datetime.now(timezone.utc)

        trigger_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
        )
        # Completion visit belongs to a DIFFERENT patient.
        other_patient_visit = _make_visit(
            db_session, tenant_id, other_patient, other_admission, rn_user_id,
            visit_type="SKILLED_NURSING", visit_discipline="RN",
            visit_datetime=now + timedelta(hours=6),
        )

        outcome = _trigger_requirement(db_session, tenant_id, patient, trigger_visit.id, now)

        with pytest.raises(ValueError, match="does not belong to this patient"):
            complete_sfv_requirement_from_visit(
                db=db_session,
                sfv_requirement_id=outcome.requirement_id,
                completing_visit_id=other_patient_visit.id,
                completing_visit_datetime=other_patient_visit.visit_datetime,
                discipline="RN",
                visit_mode="IN_PERSON",
            )

    def test_completion_visit_not_found_rejected(self, db_session, tenant, rn_user_id):
        tenant_id = uuid.UUID(tenant.id)
        patient, admission = _make_patient_and_admission(db_session, tenant_id)
        now = datetime.now(timezone.utc)

        trigger_visit = _make_visit(
            db_session, tenant_id, patient, admission, rn_user_id,
            visit_type="RNICA_ADMISSION", visit_discipline="RN", visit_datetime=now,
        )
        outcome = _trigger_requirement(db_session, tenant_id, patient, trigger_visit.id, now)

        with pytest.raises(ValueError, match="Completion visit not found"):
            complete_sfv_requirement_from_visit(
                db=db_session,
                sfv_requirement_id=outcome.requirement_id,
                completing_visit_id=uuid.uuid4(),
                completing_visit_datetime=now + timedelta(hours=6),
                discipline="RN",
                visit_mode="IN_PERSON",
            )
