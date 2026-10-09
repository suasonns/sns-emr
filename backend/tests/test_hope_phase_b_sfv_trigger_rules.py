"""Direct engine-level tests for the CMS HOPE SFV activation rules in
``app.services.hope_phase_b_engine``.

Owner directive (GI SFV CMS Compliance Correction -- Gastrointestinal
governance review, 2026-10-06) required direct tests -- not just code
inspection -- proving:

  1. SFV only originates from a qualifying HOPE timepoint
     (INITIAL_RN_ICA, HUV1, HUV2) -- an invalid trigger_source_type is
     rejected outright.
  2. Moderate J2051 impact activates the requirement.
  3. Severe J2051 impact activates the requirement.
  4. Mild impact does NOT activate the requirement.
  5. None/not-assessed impact does NOT activate the requirement.
  6. Exactly one SFVRequirement is created per qualifying timepoint, even
     when called again for the same (trigger_source_type,
     trigger_reference_id) pair.
  7. Multiple triggering symptoms (pain AND non-pain both
     Moderate/Severe at the same timepoint) attach to the SAME single
     SFVRequirement (trigger_symptom_group == "BOTH"), not two.
  8. The SFV due date is exactly 2 calendar days after the triggering
     assessment datetime.
  9. HUV1 can create its own SFV requirement, independent of any
     INITIAL_RN_ICA requirement for the same patient.
 10. HUV2 can create its own SFV requirement, independent of any HUV1
     requirement for the same patient.
 11. J2053 (the SFV's own reassessment) cannot recursively create a new
     CMS SFV requirement -- "SFV" is not a valid trigger_source_type,
     so attempting to re-trigger from the SFV visit itself is rejected
     by the engine, structurally preventing recursion.

These are read-only engine-level tests (no HTTP layer) so failures
point directly at hope_phase_b_engine.py rather than at routing/auth
concerns already covered by test_sfv_completion_api.py and friends.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models.admission import Admission
from app.models.patient import Patient
from app.models.sfv_requirement import SFVRequirement
from app.services.hope_phase_b_engine import (
    SOURCE_HUV1,
    SOURCE_HUV2,
    SOURCE_INITIAL_RN_ICA,
    create_huv_tasks_from_initial_rn_ica,
    maybe_trigger_sfv_from_hope_timepoint,
    process_huv_finalize,
    process_initial_rn_ica_finalize,
    validate_huv_visit_completion,
)
from tests.conftest import _test_tenant_id


def _tenant_id():
    return uuid.UUID(_test_tenant_id())


def _make_patient_and_admission(db_session):
    tenant_id = _tenant_id()
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"SFV-RULES-{uuid.uuid4().hex[:10]}",
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


# ════════════════════════════════════════════════════════════════
# 1. Invalid trigger_source_type is rejected (qualifying timepoint only)
# ════════════════════════════════════════════════════════════════

def test_invalid_trigger_source_type_is_rejected(db_session):
    patient, _ = _make_patient_and_admission(db_session)
    now = datetime.now(timezone.utc)
    with pytest.raises(ValueError, match="INITIAL_RN_ICA, HUV1, or HUV2"):
        maybe_trigger_sfv_from_hope_timepoint(
            db=db_session,
            tenant_id=_tenant_id(),
            patient_id=patient.id,
            trigger_source_type="RECERT",
            trigger_reference_id=uuid.uuid4(),
            trigger_datetime=now,
            pain_impact="SEVERE",
            non_pain_impact=None,
        )


def test_sfv_trigger_source_type_rejects_recursive_sfv_source(db_session):
    """J2053 non-recursion: the SFV's own reassessment visit cannot be
    used as a trigger source for a brand-new CMS SFV requirement --
    "SFV" is not an accepted trigger_source_type."""
    patient, _ = _make_patient_and_admission(db_session)
    now = datetime.now(timezone.utc)
    with pytest.raises(ValueError, match="INITIAL_RN_ICA, HUV1, or HUV2"):
        maybe_trigger_sfv_from_hope_timepoint(
            db=db_session,
            tenant_id=_tenant_id(),
            patient_id=patient.id,
            trigger_source_type="SFV",
            trigger_reference_id=uuid.uuid4(),
            trigger_datetime=now,
            pain_impact="SEVERE",
            non_pain_impact=None,
        )


# ════════════════════════════════════════════════════════════════
# 2-5. Moderate/Severe activate; Mild/None do not
# ════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("impact", ["MODERATE", "SEVERE"])
def test_moderate_or_severe_impact_activates_sfv(db_session, impact):
    patient, _ = _make_patient_and_admission(db_session)
    now = datetime.now(timezone.utc)
    outcome = maybe_trigger_sfv_from_hope_timepoint(
        db=db_session,
        tenant_id=_tenant_id(),
        patient_id=patient.id,
        trigger_source_type=SOURCE_INITIAL_RN_ICA,
        trigger_reference_id=uuid.uuid4(),
        trigger_datetime=now,
        pain_impact=impact,
        non_pain_impact=None,
    )
    assert outcome.created is True, outcome.reason
    assert outcome.requirement_id is not None


@pytest.mark.parametrize("impact", ["MILD", "NONE", None, "UNABLE_TO_DETERMINE"])
def test_mild_or_none_impact_does_not_activate_sfv(db_session, impact):
    patient, _ = _make_patient_and_admission(db_session)
    now = datetime.now(timezone.utc)
    outcome = maybe_trigger_sfv_from_hope_timepoint(
        db=db_session,
        tenant_id=_tenant_id(),
        patient_id=patient.id,
        trigger_source_type=SOURCE_INITIAL_RN_ICA,
        trigger_reference_id=uuid.uuid4(),
        trigger_datetime=now,
        pain_impact=impact,
        non_pain_impact=None,
    )
    assert outcome.created is False, (
        f"impact={impact!r} must NOT activate an SFV requirement; "
        f"got created=True, reason={outcome.reason!r}"
    )
    assert outcome.requirement_id is None


# ════════════════════════════════════════════════════════════════
# 6. Exactly one SFVRequirement per qualifying timepoint (dedup)
# ════════════════════════════════════════════════════════════════

def test_one_sfv_requirement_per_qualifying_timepoint(db_session):
    patient, _ = _make_patient_and_admission(db_session)
    now = datetime.now(timezone.utc)
    trigger_visit_id = uuid.uuid4()

    first = maybe_trigger_sfv_from_hope_timepoint(
        db=db_session,
        tenant_id=_tenant_id(),
        patient_id=patient.id,
        trigger_source_type=SOURCE_INITIAL_RN_ICA,
        trigger_reference_id=trigger_visit_id,
        trigger_datetime=now,
        pain_impact="SEVERE",
        non_pain_impact=None,
    )
    assert first.created is True

    # Calling again for the SAME (trigger_source_type, trigger_reference_id)
    # -- e.g. a re-save of the same assessment -- must not create a
    # second requirement.
    second = maybe_trigger_sfv_from_hope_timepoint(
        db=db_session,
        tenant_id=_tenant_id(),
        patient_id=patient.id,
        trigger_source_type=SOURCE_INITIAL_RN_ICA,
        trigger_reference_id=trigger_visit_id,
        trigger_datetime=now,
        pain_impact="SEVERE",
        non_pain_impact=None,
    )
    assert second.created is False
    assert second.requirement_id == first.requirement_id

    count = (
        db_session.query(SFVRequirement)
        .filter(SFVRequirement.patient_id == patient.id)
        .filter(SFVRequirement.trigger_source_type == SOURCE_INITIAL_RN_ICA)
        .filter(SFVRequirement.trigger_reference_id == trigger_visit_id)
        .count()
    )
    assert count == 1


# ════════════════════════════════════════════════════════════════
# 7. Multiple triggering symptoms attach to the SAME single SFV
# ════════════════════════════════════════════════════════════════

def test_multiple_triggering_symptoms_attach_to_one_sfv(db_session):
    patient, _ = _make_patient_and_admission(db_session)
    now = datetime.now(timezone.utc)
    trigger_visit_id = uuid.uuid4()

    outcome = maybe_trigger_sfv_from_hope_timepoint(
        db=db_session,
        tenant_id=_tenant_id(),
        patient_id=patient.id,
        trigger_source_type=SOURCE_HUV1,
        trigger_reference_id=trigger_visit_id,
        trigger_datetime=now,
        pain_impact="MODERATE",
        non_pain_impact="SEVERE",
    )
    assert outcome.created is True

    requirement = (
        db_session.query(SFVRequirement)
        .filter(SFVRequirement.id == uuid.UUID(outcome.requirement_id))
        .one()
    )
    assert requirement.trigger_symptom_group == "BOTH"

    count = (
        db_session.query(SFVRequirement)
        .filter(SFVRequirement.patient_id == patient.id)
        .filter(SFVRequirement.trigger_reference_id == trigger_visit_id)
        .count()
    )
    assert count == 1, "Exactly one SFVRequirement must cover both triggering symptoms"


# ════════════════════════════════════════════════════════════════
# 8. Due date is exactly 2 calendar days after the trigger
# ════════════════════════════════════════════════════════════════

def test_sfv_due_date_is_two_calendar_days_after_trigger(db_session):
    patient, _ = _make_patient_and_admission(db_session)
    trigger_datetime = datetime(2026, 3, 10, 14, 30, tzinfo=timezone.utc)
    outcome = maybe_trigger_sfv_from_hope_timepoint(
        db=db_session,
        tenant_id=_tenant_id(),
        patient_id=patient.id,
        trigger_source_type=SOURCE_INITIAL_RN_ICA,
        trigger_reference_id=uuid.uuid4(),
        trigger_datetime=trigger_datetime,
        pain_impact="SEVERE",
        non_pain_impact=None,
    )
    assert outcome.created is True
    requirement = (
        db_session.query(SFVRequirement)
        .filter(SFVRequirement.id == uuid.UUID(outcome.requirement_id))
        .one()
    )
    assert requirement.due_at == trigger_datetime + timedelta(days=2)


# ════════════════════════════════════════════════════════════════
# 9-10. HUV1 and HUV2 each create their own independent SFV
# ════════════════════════════════════════════════════════════════

def test_huv1_and_huv2_each_create_independent_sfv_requirements(db_session):
    patient, _ = _make_patient_and_admission(db_session)
    election_datetime = datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc)

    # Seed the HUV1/HUV2 tasks the way INITIAL_RN_ICA finalize would.
    create_huv_tasks_from_initial_rn_ica(
        db=db_session,
        tenant_id=_tenant_id(),
        patient_id=patient.id,
        initial_rn_ica_visit_id=uuid.uuid4(),
        election_datetime=election_datetime,
    )

    huv1_visit_id = uuid.uuid4()
    huv1_datetime = election_datetime + timedelta(days=10)  # within day 6-15 window
    huv1_result = process_huv_finalize(
        db=db_session,
        tenant_id=_tenant_id(),
        patient_id=patient.id,
        huv_task_type=SOURCE_HUV1,
        huv_visit_id=huv1_visit_id,
        election_datetime=election_datetime,
        completed_visit_datetime=huv1_datetime,
        discipline="RN",
        j2051_pain_impact=None,
        j2051_non_pain_impact="MODERATE",
    )
    assert huv1_result.created is True

    huv2_visit_id = uuid.uuid4()
    huv2_datetime = election_datetime + timedelta(days=20)  # within day 16-30 window
    huv2_result = process_huv_finalize(
        db=db_session,
        tenant_id=_tenant_id(),
        patient_id=patient.id,
        huv_task_type=SOURCE_HUV2,
        huv_visit_id=huv2_visit_id,
        election_datetime=election_datetime,
        completed_visit_datetime=huv2_datetime,
        discipline="RN",
        j2051_pain_impact=None,
        j2051_non_pain_impact="SEVERE",
    )
    assert huv2_result.created is True
    assert huv2_result.requirement_id != huv1_result.requirement_id

    huv1_requirement = (
        db_session.query(SFVRequirement)
        .filter(SFVRequirement.id == uuid.UUID(huv1_result.requirement_id))
        .one()
    )
    huv2_requirement = (
        db_session.query(SFVRequirement)
        .filter(SFVRequirement.id == uuid.UUID(huv2_result.requirement_id))
        .one()
    )
    assert huv1_requirement.trigger_source_type == SOURCE_HUV1
    assert huv1_requirement.due_at == huv1_datetime + timedelta(days=2)
    assert huv2_requirement.trigger_source_type == SOURCE_HUV2
    assert huv2_requirement.due_at == huv2_datetime + timedelta(days=2)


def test_huv_visit_completion_outside_window_is_rejected(db_session):
    election_datetime = datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc)
    # Day 20 is outside the HUV1 (day 6-15) window.
    with pytest.raises(ValueError, match="HUV1 must be completed"):
        validate_huv_visit_completion(
            election_datetime=election_datetime,
            completed_visit_datetime=election_datetime + timedelta(days=20),
            discipline="RN",
            task_type_name=SOURCE_HUV1,
        )
    # Day 5 is outside the HUV2 (day 16-30) window.
    with pytest.raises(ValueError, match="HUV2 must be completed"):
        validate_huv_visit_completion(
            election_datetime=election_datetime,
            completed_visit_datetime=election_datetime + timedelta(days=5),
            discipline="RN",
            task_type_name=SOURCE_HUV2,
        )


# ════════════════════════════════════════════════════════════════
# 11. INITIAL_RN_ICA finalize both seeds HUV1/HUV2 tasks and can
#     independently trigger its own SFV requirement.
# ════════════════════════════════════════════════════════════════

def test_initial_rn_ica_finalize_creates_huv_tasks_and_own_sfv(db_session):
    patient, _ = _make_patient_and_admission(db_session)
    election_datetime = datetime(2026, 2, 1, 8, 0, tzinfo=timezone.utc)
    visit_id = uuid.uuid4()

    result = process_initial_rn_ica_finalize(
        db=db_session,
        tenant_id=_tenant_id(),
        patient_id=patient.id,
        initial_rn_ica_visit_id=visit_id,
        election_datetime=election_datetime,
        j2051_pain_impact="SEVERE",
        j2051_non_pain_impact=None,
    )
    assert result["huv1_task_id"] is not None
    assert result["huv2_task_id"] is not None
    assert result["sfv_created"] is True

    requirement = (
        db_session.query(SFVRequirement)
        .filter(SFVRequirement.id == uuid.UUID(result["sfv_requirement_id"]))
        .one()
    )
    assert requirement.trigger_source_type == SOURCE_INITIAL_RN_ICA
    assert requirement.due_at == election_datetime + timedelta(days=2)
