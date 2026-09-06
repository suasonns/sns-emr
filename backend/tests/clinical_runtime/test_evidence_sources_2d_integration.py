# tests/clinical_runtime/test_evidence_sources_2d_integration.py
"""
Commit 2D (corrected) tests: structured conflict detection with a policy
registry gate (evidence_conflict_detection.detect_functional_score_conflicts
/ detect_missing_rn_recert_requirement), the SourceCapability registry, the
EvidencePolarity contract (default NEUTRAL, EXPLICIT_NEGATIVE requires
authoritative source identity), and the harvester's canonical
(non-UUID-lexical) chronology ordering -- against a real, migrated isolated
database via tests/conftest.py `db_session` -- no mocking.

ENGINEERING CORRECTION CONTEXT: the original Commit 2D shipped an
unapproved "same day = conflict, different day = trend" timing policy.
That policy has been removed. Every InstrumentComparisonPolicy and
EvidenceRequirementPolicy in evidence_conflict_detection.py is DRAFT and
inactive; this test file verifies the SAFE FALLBACK behavior that applies
while that remains true:
  - any genuine value disagreement (same date, different date, or missing
    date) between independently-sourced items is POTENTIAL_CONFLICT,
    UNRESOLVED, human_review_required=True, winning_evidence_id=None --
    never auto-classified more specifically;
  - no formal MissingEvidenceRequirement is ever generated; a
    RequirementPolicyNotice(status="POLICY_NOT_CONFIGURED") is returned
    instead whenever a benefit_period_id is explicitly scoped.

Covers the corrected Commit 2D acceptance criteria:
  - DOCUMENTED_STATUS_PRESERVED_WHEN_CONFLICTING
  - STRUCTURED_CONFLICT_REFERENCES_BOTH_ITEMS
  - SAME_VALUE_IS_NOT_A_CONFLICT
  - SAME_DATE_DIFFERENT_VALUE_IS_NOT_AUTOMATICALLY_VALUE_DISAGREEMENT
  - DIFFERENT_DATES_ARE_NOT_AUTOMATICALLY_A_TREND
  - MISSING_EFFECTIVE_AT_IS_POTENTIAL_CONFLICT
  - NO_AUTOMATIC_WINNER / HUMAN_REVIEW_REQUIRED
  - CONFLICT_COMPARISON_SCOPED_TO_BENEFIT_PERIOD (+ tenant/instrument
    identity via the pure-function unit tests)
  - ECOG_CROSS_SOURCE_COMPARISON_NOT_ATTEMPTED (FIELD_NOT_AVAILABLE via the
    SourceCapability registry, not fabricated)
  - NO_APPROVED_REQUIREMENT_POLICY_YIELDS_POLICY_NOT_CONFIGURED
  - UNAPPROVED_REQUIREMENT_POLICY_NEVER_CREATES_FORMAL_MISSING_REQUIREMENT
  - REQUIREMENT_NOTICE_NOT_PRODUCED_WITHOUT_EXPLICIT_BENEFIT_PERIOD_SCOPE
  - DEFAULT_POLARITY_IS_NEUTRAL
  - NULL_IS_NOT_POSITIVE / NULL_IS_NOT_NEGATIVE
  - EXPLICIT_NEGATIVE_POLARITY_REQUIRES_COMPLETE_SOURCE_IDENTITY
  - EXPLICIT_POSITIVE_POLARITY_CAN_BE_SET_EXPLICITLY
  - POLICY_CANNOT_BE_APPROVED_WITHOUT_APPROVED_BY_AND_APPROVED_AT
  - BUNDLE_CHRONOLOGICAL_ORDERS_BY_EFFECTIVE_AT_NOT_EVIDENCE_ID
  - HARVESTER_ORDERING_DOES_NOT_DEPEND_ON_UUID_LEXICAL_ORDER
  - DOCUMENTED_OBSERVATIONS_REMAIN_DOCUMENTED
  - NO_AUTONOMOUS_ELIGIBILITY/CERTIFICATION/RECERTIFICATION/PROGNOSIS/
    DISCHARGE conclusion anywhere in conflict/requirement-notice output

Explicitly out of scope / N/A (documented rather than fabricated):
  - "RNRecertAssessment ECOG vs F2FEncounter ECOG" conflict detection:
    RNRecertAssessment has no ecog_score_* field at all -- registered as
    CapabilityStatus.FIELD_NOT_AVAILABLE, not tested as a conflict because
    there is nothing to compare.
  - Correction/addendum/entered-in-error relationship tests for
    RNRecertAssessment or F2FEncounter: neither model has any such field.
    Certification's real supersession chain is already covered by the
    existing Commit 2B tests (correction_status="SUPERSEDED") and is not
    duplicated here; this file's correction_states/supersession_states
    fields on ClinicalEvidenceConflict are exercised via the RN/F2F pair,
    which legitimately reports "FIELD_NOT_AVAILABLE" / "NOT_SUPERSEDED".
  - No InstrumentComparisonPolicy or EvidenceRequirementPolicy is ever
    activated in this test file -- activation requires a real clinical/
    agency approval outside engineering's authority.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest

from app.domain.clinical_runtime.contracts import (
    CapabilityStatus,
    ClinicalEvidenceBundle,
    ClinicalEvidenceItem,
    ClinicalSourceReference,
    ConflictResolutionStatus,
    ConflictType,
    EvidenceOrigin,
    EvidencePolarity,
    EvidenceRequirementPolicy,
    EvidenceStatus,
    InstrumentComparisonPolicy,
    PolicyApprovalStatus,
    SourceCapability,
)
from app.models.benefit_period import BenefitPeriod
from app.models.f2f_encounter import F2FEncounter
from app.models.patient import Patient
from app.models.rn_recert_assessment import RNRecertAssessment
from app.services.eligibility.clinical_evidence_harvester import ClinicalEvidenceHarvester
from app.services.eligibility.evidence_conflict_detection import (
    EVIDENCE_REQUIREMENT_POLICIES,
    INSTRUMENT_COMPARISON_POLICIES,
    detect_functional_score_conflicts,
    detect_missing_rn_recert_requirement,
    get_capability,
)

_TEST_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")

_FORBIDDEN_CONCLUSION_TERMS = (
    "eligib",
    "certif",
    "recertif",
    "prognosis",
    "discharge",
    "terminal status",
)


def _assert_no_conclusion_language(*texts: str) -> None:
    for text in texts:
        if not text:
            continue
        lowered = text.lower()
        for term in _FORBIDDEN_CONCLUSION_TERMS:
            assert term not in lowered, f"forbidden conclusion term {term!r} found in {text!r}"


def _seed_id(test_name: str, kind: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"commit2dfix:{test_name}:{kind}")


def _seed_patient(db_session, test_name, tenant_id):
    patient_id = _seed_id(test_name, "patient")
    if db_session.get(Patient, patient_id) is None:
        db_session.add(
            Patient(
                id=patient_id,
                tenant_id=tenant_id,
                mrn=f"MRN-{test_name}",
                date_of_birth=date(1945, 6, 1),
                primary_diagnosis="Adult Failure to Thrive",
            )
        )
        db_session.commit()
    return patient_id


def _seed_benefit_period(db_session, test_name, suffix, *, patient_id, tenant_id, **fields):
    bp_id = _seed_id(test_name, f"bp_{suffix}")
    if db_session.get(BenefitPeriod, bp_id) is None:
        defaults = dict(
            benefit_type="INITIAL",
            period_number=1,
            election_date=date(2025, 1, 1),
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 1),
            is_current=True,
        )
        defaults.update(fields)
        db_session.add(
            BenefitPeriod(id=bp_id, tenant_id=tenant_id, patient_id=patient_id, **defaults)
        )
        db_session.commit()
    return bp_id


def _seed_assessment(db_session, test_name, suffix, *, patient_id, benefit_period_id, tenant_id, **fields):
    row_id = _seed_id(test_name, f"assess_{suffix}")
    if db_session.get(RNRecertAssessment, row_id) is None:
        defaults = dict(
            created_by_user_id=_TEST_USER_ID,
            tenant_id=tenant_id,
            status="FINALIZED",
            pps_score=40,
            kps_score=40,
            fast_stage="7C",
            adl_level="TOTAL_DEPENDENCE",
            adl_dependency_count=6,
            primary_diagnosis="Adult Failure to Thrive",
            attested_at=datetime(2025, 2, 1, tzinfo=timezone.utc),
            attesting_provider_user_id=_TEST_USER_ID,
        )
        defaults.update(fields)
        db_session.add(
            RNRecertAssessment(
                id=row_id,
                patient_id=patient_id,
                benefit_period_id=benefit_period_id,
                **defaults,
            )
        )
        db_session.commit()
    return row_id


def _seed_f2f(db_session, test_name, suffix, *, patient_id, benefit_period_id, tenant_id, **fields):
    row_id = _seed_id(test_name, f"f2f_{suffix}")
    if db_session.get(F2FEncounter, row_id) is None:
        defaults = dict(
            encounter_date=date(2025, 2, 1),
            performed_by_role="MD",
            performed_by_user_id=_TEST_USER_ID,
            status="FINALIZED",
            pps_score_previous=60,
            pps_score_current=40,
        )
        defaults.update(fields)
        db_session.add(
            F2FEncounter(
                id=row_id,
                tenant_id=tenant_id,
                patient_id=patient_id,
                benefit_period_id=benefit_period_id,
                **defaults,
            )
        )
        db_session.commit()
    return row_id


def _source_ref(**overrides):
    defaults = dict(
        source_type="DATABASE_RECORD",
        source_id="row-1",
        source_record_type="TEST_RECORD",
        source_field="test_field",
        source_model="TestModel",
        source_table="test_models",
        source_patient_id=None,
    )
    defaults.update(overrides)
    return ClinicalSourceReference(**defaults)


# ---------------------------------------------------------------------
# Policy registries -- must all remain DRAFT/inactive
# ---------------------------------------------------------------------


def test_all_instrument_comparison_policies_are_draft_and_inactive():
    for instrument, policy in INSTRUMENT_COMPARISON_POLICIES.items():
        assert policy.approval_status == PolicyApprovalStatus.DRAFT
        assert policy.is_active() is False


def test_all_evidence_requirement_policies_are_draft_and_inactive():
    for workflow, policy in EVIDENCE_REQUIREMENT_POLICIES.items():
        assert policy.approval_status == PolicyApprovalStatus.DRAFT
        assert policy.is_active() is False


def test_policy_cannot_be_approved_without_approved_by_and_approved_at():
    with pytest.raises(ValueError, match="cannot be APPROVED"):
        InstrumentComparisonPolicy(
            policy_id="pps-test",
            policy_version="1.0",
            instrument="PPS",
            approval_status=PolicyApprovalStatus.APPROVED,
        )
    with pytest.raises(ValueError, match="cannot be APPROVED"):
        EvidenceRequirementPolicy(
            policy_id="rn-recert-test",
            policy_version="1.0",
            workflow="RN_RECERT_ASSESSMENT",
            approval_status=PolicyApprovalStatus.APPROVED,
        )


def test_approved_policy_requires_both_fields_together():
    # A fully-specified, properly-approved policy IS constructible -- this
    # module just never constructs one for a real instrument/workflow.
    policy = InstrumentComparisonPolicy(
        policy_id="pps-test-approved",
        policy_version="1.0",
        instrument="PPS",
        approval_status=PolicyApprovalStatus.APPROVED,
        approved_by="test-reviewer",
        approved_at=datetime.now(timezone.utc),
    )
    assert policy.is_active() is True


# ---------------------------------------------------------------------
# SourceCapability registry
# ---------------------------------------------------------------------


def test_ecog_capability_is_field_not_available_on_rn_recert_assessment():
    capability = get_capability("RNRecertAssessment", "ecog_score")
    assert capability.status == CapabilityStatus.FIELD_NOT_AVAILABLE


def test_pps_capability_is_available_on_both_sources():
    assert get_capability("RNRecertAssessment", "pps_score").status == CapabilityStatus.AVAILABLE
    assert get_capability("F2FEncounter", "pps_score_current").status == CapabilityStatus.AVAILABLE


def test_unregistered_field_defaults_to_field_not_available():
    capability = get_capability("SomeUnknownModel", "some_unknown_field")
    assert capability.status == CapabilityStatus.FIELD_NOT_AVAILABLE


# ---------------------------------------------------------------------
# Structured conflict detection -- SAFE FALLBACK (no approved policy)
# ---------------------------------------------------------------------


def test_documented_items_remain_documented_when_conflicting(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "conflict_status_preserved", tenant_id)
    bp_id = _seed_benefit_period(db_session, "conflict_status_preserved", "a", patient_id=patient_id, tenant_id=tenant_id)
    _seed_assessment(
        db_session, "conflict_status_preserved", "a", patient_id=patient_id, benefit_period_id=bp_id,
        tenant_id=tenant_id, pps_score=40, attested_at=datetime(2025, 2, 1, tzinfo=timezone.utc),
    )
    _seed_f2f(
        db_session, "conflict_status_preserved", "a", patient_id=patient_id, benefit_period_id=bp_id,
        tenant_id=tenant_id, pps_score_current=70, encounter_date=date(2025, 2, 1),
    )

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=bp_id)
    assert len(bundle.conflicts) == 1
    for item in bundle.items:
        assert item.status == EvidenceStatus.DOCUMENTED


def test_structured_conflict_references_both_source_items_and_selects_no_winner(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "conflict_refs_both", tenant_id)
    bp_id = _seed_benefit_period(db_session, "conflict_refs_both", "a", patient_id=patient_id, tenant_id=tenant_id)
    rn_id = _seed_assessment(
        db_session, "conflict_refs_both", "a", patient_id=patient_id, benefit_period_id=bp_id,
        tenant_id=tenant_id, pps_score=40, attested_at=datetime(2025, 2, 1, tzinfo=timezone.utc),
    )
    f2f_id = _seed_f2f(
        db_session, "conflict_refs_both", "a", patient_id=patient_id, benefit_period_id=bp_id,
        tenant_id=tenant_id, pps_score_current=70, encounter_date=date(2025, 2, 1),
    )

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=bp_id)
    conflict = bundle.conflicts[0]
    assert conflict.concept_code == "PPS"
    assert set(conflict.evidence_ids) == {
        f"rn_recert_assessments:{rn_id}",
        f"f2f_encounters:{f2f_id}",
    }
    assert conflict.tenant_id == tenant_id
    assert conflict.benefit_period_id == bp_id
    assert set(conflict.source_models) == {"RNRecertAssessment", "F2FEncounter"}
    assert conflict.observed_values in ([40, 70], [70, 40])
    assert conflict.resolution_status == ConflictResolutionStatus.UNRESOLVED
    assert conflict.human_review_required is True
    assert conflict.winning_evidence_id is None
    assert conflict.resolved_at is None


def test_same_value_across_sources_is_not_a_conflict(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "conflict_same_value", tenant_id)
    bp_id = _seed_benefit_period(db_session, "conflict_same_value", "a", patient_id=patient_id, tenant_id=tenant_id)
    _seed_assessment(
        db_session, "conflict_same_value", "a", patient_id=patient_id, benefit_period_id=bp_id,
        tenant_id=tenant_id, pps_score=40, attested_at=datetime(2025, 2, 1, tzinfo=timezone.utc),
    )
    _seed_f2f(
        db_session, "conflict_same_value", "a", patient_id=patient_id, benefit_period_id=bp_id,
        tenant_id=tenant_id, pps_score_current=40, encounter_date=date(2025, 2, 1),
    )

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=bp_id)
    assert bundle.conflicts == []


def test_same_date_different_value_is_potential_conflict_not_value_disagreement(db_session):
    """Same effective date used to be auto-classified as VALUE_DISAGREEMENT
    -- that was an unapproved policy decision and has been removed. Without
    an APPROVED InstrumentComparisonPolicy, this must be POTENTIAL_CONFLICT."""
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "conflict_same_date", tenant_id)
    bp_id = _seed_benefit_period(db_session, "conflict_same_date", "a", patient_id=patient_id, tenant_id=tenant_id)
    _seed_assessment(
        db_session, "conflict_same_date", "a", patient_id=patient_id, benefit_period_id=bp_id,
        tenant_id=tenant_id, pps_score=40, attested_at=datetime(2025, 2, 1, tzinfo=timezone.utc),
    )
    _seed_f2f(
        db_session, "conflict_same_date", "a", patient_id=patient_id, benefit_period_id=bp_id,
        tenant_id=tenant_id, pps_score_current=70, encounter_date=date(2025, 2, 1),
    )

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=bp_id)
    assert len(bundle.conflicts) == 1
    conflict = bundle.conflicts[0]
    assert conflict.conflict_type == ConflictType.POTENTIAL_CONFLICT
    assert "NO_APPROVED_COMPARISON_POLICY" in conflict.warning_codes


def test_different_dates_different_value_is_not_automatically_a_trend(db_session):
    """Different effective dates used to be silently treated as a "trend"
    (no conflict object at all) -- that was also an unapproved policy
    decision. Without an APPROVED policy, this must still surface as a
    POTENTIAL_CONFLICT, never silently dropped."""
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "conflict_diff_dates", tenant_id)
    bp_id = _seed_benefit_period(db_session, "conflict_diff_dates", "a", patient_id=patient_id, tenant_id=tenant_id)
    _seed_assessment(
        db_session, "conflict_diff_dates", "a", patient_id=patient_id, benefit_period_id=bp_id,
        tenant_id=tenant_id, pps_score=60, attested_at=datetime(2025, 1, 15, tzinfo=timezone.utc),
    )
    _seed_f2f(
        db_session, "conflict_diff_dates", "a", patient_id=patient_id, benefit_period_id=bp_id,
        tenant_id=tenant_id, pps_score_current=40, encounter_date=date(2025, 2, 15),
    )

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=bp_id)
    assert len(bundle.conflicts) == 1
    conflict = bundle.conflicts[0]
    assert conflict.conflict_type == ConflictType.POTENTIAL_CONFLICT
    # Both observations remain present as ordinary evidence regardless.
    values = {item.normalized_value.get("pps_score") or item.normalized_value.get("pps_score_current") for item in bundle.items}
    assert values == {60, 40}


def test_missing_effective_at_on_either_side_is_potential_conflict(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "conflict_missing_eff", tenant_id)
    bp_id = _seed_benefit_period(db_session, "conflict_missing_eff", "a", patient_id=patient_id, tenant_id=tenant_id)
    _seed_assessment(
        db_session, "conflict_missing_eff", "a", patient_id=patient_id, benefit_period_id=bp_id,
        tenant_id=tenant_id, pps_score=40, attested_at=None, finalized_at=None,
    )
    _seed_f2f(
        db_session, "conflict_missing_eff", "a", patient_id=patient_id, benefit_period_id=bp_id,
        tenant_id=tenant_id, pps_score_current=70, encounter_date=date(2025, 2, 1),
    )

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=bp_id)
    assert len(bundle.conflicts) == 1
    conflict = bundle.conflicts[0]
    assert conflict.conflict_type == ConflictType.POTENTIAL_CONFLICT
    assert conflict.human_review_required is True


def test_conflict_comparison_is_scoped_to_benefit_period(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "conflict_bp_scope", tenant_id)
    bp_1 = _seed_benefit_period(db_session, "conflict_bp_scope", "1", patient_id=patient_id, tenant_id=tenant_id, period_number=1)
    bp_2 = _seed_benefit_period(
        db_session, "conflict_bp_scope", "2", patient_id=patient_id, tenant_id=tenant_id,
        benefit_type="RECERT", period_number=2, election_date=date(2025, 3, 1),
        start_date=date(2025, 3, 1), end_date=date(2025, 5, 1),
    )
    _seed_assessment(
        db_session, "conflict_bp_scope", "1", patient_id=patient_id, benefit_period_id=bp_1,
        tenant_id=tenant_id, pps_score=40, attested_at=datetime(2025, 2, 1, tzinfo=timezone.utc),
    )
    _seed_f2f(
        db_session, "conflict_bp_scope", "2", patient_id=patient_id, benefit_period_id=bp_2,
        tenant_id=tenant_id, pps_score_current=70, encounter_date=date(2025, 2, 1),
    )

    bundle_all = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id)
    # Different benefit periods -- never compared against each other even
    # though the effective dates coincidentally match.
    assert bundle_all.conflicts == []


def test_ecog_has_no_cross_source_comparison_available(db_session):
    """ECOG only exists on F2FEncounter -- FIELD_NOT_AVAILABLE (via
    SourceCapability) on the RN side, so no ECOG conflict can ever be
    produced regardless of values."""
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "ecog_no_comparison", tenant_id)
    bp_id = _seed_benefit_period(db_session, "ecog_no_comparison", "a", patient_id=patient_id, tenant_id=tenant_id)
    _seed_f2f(
        db_session, "ecog_no_comparison", "a", patient_id=patient_id, benefit_period_id=bp_id,
        tenant_id=tenant_id, ecog_score_current=3, encounter_date=date(2025, 2, 1),
    )

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=bp_id)
    assert all(c.instrument != "ECOG" for c in bundle.conflicts)


# ---------------------------------------------------------------------
# Missing-workflow-requirement -- SAFE FALLBACK: notice only, never a
# fabricated formal requirement.
# ---------------------------------------------------------------------


def test_no_approved_requirement_policy_yields_policy_not_configured_notice(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "requirement_notice_present", tenant_id)
    bp_id = _seed_benefit_period(db_session, "requirement_notice_present", "a", patient_id=patient_id, tenant_id=tenant_id)
    # No RNRecertAssessment seeded for this benefit period at all.

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=bp_id)
    assert bundle.missing_requirements == []
    assert len(bundle.requirement_policy_notices) == 1
    notice = bundle.requirement_policy_notices[0]
    assert notice.workflow == "RN_RECERT_ASSESSMENT"
    assert notice.status == "POLICY_NOT_CONFIGURED"


def test_requirement_notice_not_produced_without_explicit_benefit_period_scope(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "requirement_notice_unscoped", tenant_id)
    _seed_benefit_period(db_session, "requirement_notice_unscoped", "a", patient_id=patient_id, tenant_id=tenant_id)

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id)
    assert bundle.missing_requirements == []
    assert bundle.requirement_policy_notices == []


def test_no_formal_missing_requirement_even_when_assessment_is_absent(db_session):
    """An unapproved EvidenceRequirementPolicy must NEVER create a formal
    MissingEvidenceRequirement -- only the inert notice above."""
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "requirement_no_formal", tenant_id)
    bp_id = _seed_benefit_period(db_session, "requirement_no_formal", "a", patient_id=patient_id, tenant_id=tenant_id)

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=bp_id)
    assert bundle.missing_requirements == []


def test_requirement_notice_still_returned_even_when_assessment_exists(db_session):
    """The notice reflects "no policy is configured", not "evidence is
    missing" -- it is returned regardless of whether an assessment exists,
    and must never be misread as a missing-evidence finding."""
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "requirement_notice_satisfied", tenant_id)
    bp_id = _seed_benefit_period(db_session, "requirement_notice_satisfied", "a", patient_id=patient_id, tenant_id=tenant_id)
    _seed_assessment(db_session, "requirement_notice_satisfied", "a", patient_id=patient_id, benefit_period_id=bp_id, tenant_id=tenant_id)

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=bp_id)
    assert bundle.missing_requirements == []
    assert len(bundle.requirement_policy_notices) == 1
    assert bundle.requirement_policy_notices[0].status == "POLICY_NOT_CONFIGURED"


# ---------------------------------------------------------------------
# EvidencePolarity contract validation (unit-level, no DB)
# ---------------------------------------------------------------------


def test_default_polarity_is_neutral():
    patient_id = uuid.uuid4()
    item = ClinicalEvidenceItem(
        evidence_id="test_models:row-1",
        patient_id=patient_id,
        concept_code="DYSPNEA",
        canonical_name="Dyspnea",
        status=EvidenceStatus.UNVERIFIED,
        source_reference=_source_ref(source_patient_id=None),
        origin=EvidenceOrigin.LEGACY_ADAPTER,
    )
    assert item.polarity == EvidencePolarity.NEUTRAL


def test_null_observed_value_is_not_inferred_as_positive_or_negative():
    patient_id = uuid.uuid4()
    item = ClinicalEvidenceItem(
        evidence_id="test_models:row-2",
        patient_id=patient_id,
        concept_code="DYSPNEA",
        canonical_name="Dyspnea",
        status=EvidenceStatus.UNVERIFIED,
        source_reference=_source_ref(source_patient_id=None),
        observed_value=None,
        origin=EvidenceOrigin.LEGACY_ADAPTER,
    )
    assert item.polarity != EvidencePolarity.POSITIVE
    assert item.polarity != EvidencePolarity.EXPLICIT_NEGATIVE
    assert item.polarity == EvidencePolarity.NEUTRAL


def test_explicit_positive_polarity_can_be_set_explicitly_with_a_mapping():
    patient_id = uuid.uuid4()
    item = ClinicalEvidenceItem(
        evidence_id="test_models:row-3",
        patient_id=patient_id,
        concept_code="DYSPNEA",
        canonical_name="Dyspnea",
        status=EvidenceStatus.DOCUMENTED,
        source_reference=_source_ref(source_patient_id=patient_id, source_model="TestModel", source_table="test_models"),
        polarity=EvidencePolarity.POSITIVE,
        observed_value="reports dyspnea on exertion",
        origin=EvidenceOrigin.AUTHORITATIVE_DATABASE,
    )
    assert item.polarity == EvidencePolarity.POSITIVE


def test_explicit_negative_polarity_rejects_legacy_adapter_origin():
    with pytest.raises(ValueError, match="EXPLICIT_NEGATIVE polarity requires origin=AUTHORITATIVE_DATABASE"):
        ClinicalEvidenceItem(
            evidence_id="x:1",
            patient_id=uuid.uuid4(),
            concept_code="DYSPNEA",
            canonical_name="Dyspnea",
            status=EvidenceStatus.UNVERIFIED,
            source_reference=_source_ref(),
            polarity=EvidencePolarity.EXPLICIT_NEGATIVE,
            origin=EvidenceOrigin.LEGACY_ADAPTER,
        )


def test_explicit_negative_polarity_requires_complete_source_identity():
    with pytest.raises(ValueError, match="requires complete source identity"):
        ClinicalEvidenceItem(
            evidence_id="x:1",
            patient_id=uuid.uuid4(),
            concept_code="DYSPNEA",
            canonical_name="Dyspnea",
            status=EvidenceStatus.UNVERIFIED,
            source_reference=_source_ref(source_model=None),
            polarity=EvidencePolarity.EXPLICIT_NEGATIVE,
            origin=EvidenceOrigin.AUTHORITATIVE_DATABASE,
        )


def test_explicit_negative_polarity_succeeds_with_complete_authoritative_source():
    patient_id = uuid.uuid4()
    item = ClinicalEvidenceItem(
        evidence_id="test_models:row-1",
        patient_id=patient_id,
        concept_code="DYSPNEA",
        canonical_name="Dyspnea",
        status=EvidenceStatus.DOCUMENTED,
        source_reference=_source_ref(source_patient_id=patient_id),
        polarity=EvidencePolarity.EXPLICIT_NEGATIVE,
        origin=EvidenceOrigin.AUTHORITATIVE_DATABASE,
        observed_value="denies dyspnea",
    )
    assert item.polarity == EvidencePolarity.EXPLICIT_NEGATIVE
    assert item.status == EvidenceStatus.DOCUMENTED


# ---------------------------------------------------------------------
# Canonical (non-UUID-lexical) chronology ordering
# ---------------------------------------------------------------------


def test_bundle_chronological_orders_by_effective_at_not_evidence_id():
    patient_id = uuid.uuid4()

    def make(evidence_id, effective_at):
        return ClinicalEvidenceItem(
            evidence_id=evidence_id,
            patient_id=patient_id,
            concept_code="PPS",
            canonical_name="PPS",
            status=EvidenceStatus.UNVERIFIED,
            source_reference=_source_ref(source_id=evidence_id),
            effective_at=effective_at,
            origin=EvidenceOrigin.LEGACY_ADAPTER,
        )

    # evidence_id "zzz_later" lexically sorts AFTER "aaa_earlier" -- but
    # "zzz_later" is the chronologically EARLIER item. A UUID/name-lexical
    # sort would get this backwards; chronological() must not.
    earlier = make("zzz_later", datetime(2025, 1, 1, tzinfo=timezone.utc))
    later = make("aaa_earlier", datetime(2025, 6, 1, tzinfo=timezone.utc))

    bundle = ClinicalEvidenceBundle(patient_id=patient_id, items=[later, earlier])
    ordered = bundle.chronological()
    assert [item.evidence_id for item in ordered] == ["zzz_later", "aaa_earlier"]


def test_harvester_ordering_does_not_depend_on_uuid_lexical_order(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "ordering_not_uuid", tenant_id)
    bp_id = _seed_benefit_period(db_session, "ordering_not_uuid", "a", patient_id=patient_id, tenant_id=tenant_id)

    # Row IDs are deterministic uuid5 hashes of the seed names below. Pick
    # whichever suffix hashes lexically LARGER and give it the EARLIER
    # attested_at, so the harvester's ordering can only be correct if it
    # follows effective_at -- a UUID-lexical sort would put them backwards.
    id_a = _seed_id("ordering_not_uuid", "assess_row_a")
    id_b = _seed_id("ordering_not_uuid", "assess_row_b")
    if str(id_a) > str(id_b):
        lexically_larger_suffix, lexically_smaller_suffix = "row_a", "row_b"
    else:
        lexically_larger_suffix, lexically_smaller_suffix = "row_b", "row_a"

    _seed_assessment(
        db_session, "ordering_not_uuid", lexically_larger_suffix, patient_id=patient_id, benefit_period_id=bp_id,
        tenant_id=tenant_id, pps_score=60, attested_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
    _seed_assessment(
        db_session, "ordering_not_uuid", lexically_smaller_suffix, patient_id=patient_id, benefit_period_id=bp_id,
        tenant_id=tenant_id, pps_score=40, attested_at=datetime(2025, 6, 1, tzinfo=timezone.utc),
    )

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=bp_id)
    items = bundle.by_concept_code("RN_RECERT_ASSESSMENT")
    # Chronological (attested_at) order is [60 (Jan), 40 (Jun)] -- the
    # lexically-larger evidence_id was given the EARLIER date, so a
    # UUID-lexical sort would have produced [40, 60] instead.
    assert [item.normalized_value["pps_score"] for item in items] == [60, 40]


# ---------------------------------------------------------------------
# No autonomous conclusion anywhere in conflict/requirement-notice output
# ---------------------------------------------------------------------


def test_no_autonomous_conclusion_in_conflict_output(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "conflict_no_conclusion", tenant_id)
    bp_id = _seed_benefit_period(db_session, "conflict_no_conclusion", "a", patient_id=patient_id, tenant_id=tenant_id)
    _seed_assessment(
        db_session, "conflict_no_conclusion", "a", patient_id=patient_id, benefit_period_id=bp_id,
        tenant_id=tenant_id, pps_score=40, attested_at=datetime(2025, 2, 1, tzinfo=timezone.utc),
    )
    _seed_f2f(
        db_session, "conflict_no_conclusion", "a", patient_id=patient_id, benefit_period_id=bp_id,
        tenant_id=tenant_id, pps_score_current=70, encounter_date=date(2025, 2, 1),
    )

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=bp_id)
    assert len(bundle.conflicts) == 1
    conflict = bundle.conflicts[0]
    _assert_no_conclusion_language(
        conflict.resolution_reason or "",
        conflict.materiality,
        " ".join(conflict.warning_codes),
    )


# ---------------------------------------------------------------------
# Pure-function unit tests (no DB) -- exercise the comparison/requirement
# logic directly, including the tenant/patient/benefit-period identity
# dimensions of conflict grouping.
# ---------------------------------------------------------------------


def _make_item(source_model, source_table, concept_code, normalized_value, *, patient_id, benefit_period_id, effective_at, evidence_id, unit=None):
    return ClinicalEvidenceItem(
        evidence_id=evidence_id,
        patient_id=patient_id,
        concept_code=concept_code,
        canonical_name=concept_code,
        status=EvidenceStatus.DOCUMENTED,
        source_reference=_source_ref(
            source_model=source_model, source_table=source_table, source_patient_id=patient_id,
        ),
        benefit_period_id=benefit_period_id,
        normalized_value=normalized_value,
        effective_at=effective_at,
        unit=unit,
        origin=EvidenceOrigin.AUTHORITATIVE_DATABASE,
    )


def test_detect_functional_score_conflicts_pure_function_is_potential_conflict():
    patient_id = uuid.uuid4()
    bp_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    items = [
        _make_item(
            "RNRecertAssessment", "rn_recert_assessments", "RN_RECERT_ASSESSMENT",
            {"pps_score": 40}, patient_id=patient_id, benefit_period_id=bp_id,
            effective_at=now, evidence_id="rn:1",
        ),
        _make_item(
            "F2FEncounter", "f2f_encounters", "F2F_ENCOUNTER",
            {"pps_score_current": 70}, patient_id=patient_id, benefit_period_id=bp_id,
            effective_at=now, evidence_id="f2f:1",
        ),
    ]
    conflicts = detect_functional_score_conflicts(items, tenant_id=uuid.uuid4())
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == ConflictType.POTENTIAL_CONFLICT
    assert conflicts[0].resolution_status == ConflictResolutionStatus.UNRESOLVED
    assert conflicts[0].winning_evidence_id is None


def test_conflict_grouping_respects_tenant_identity():
    """Passing a different tenant_id produces a differently-tagged conflict
    (tenant_id is part of the recorded conflict identity), even though this
    pure function itself receives one tenant_id per call -- per-item tenant
    scoping is enforced upstream by ClinicalEvidenceHarvester.harvest()
    before any item reaches this function."""
    patient_id = uuid.uuid4()
    bp_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    items = [
        _make_item(
            "RNRecertAssessment", "rn_recert_assessments", "RN_RECERT_ASSESSMENT",
            {"pps_score": 40}, patient_id=patient_id, benefit_period_id=bp_id,
            effective_at=now, evidence_id="rn:1",
        ),
        _make_item(
            "F2FEncounter", "f2f_encounters", "F2F_ENCOUNTER",
            {"pps_score_current": 70}, patient_id=patient_id, benefit_period_id=bp_id,
            effective_at=now, evidence_id="f2f:1",
        ),
    ]
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    conflicts_a = detect_functional_score_conflicts(items, tenant_id=tenant_a)
    conflicts_b = detect_functional_score_conflicts(items, tenant_id=tenant_b)
    assert conflicts_a[0].tenant_id == tenant_a
    assert conflicts_b[0].tenant_id == tenant_b


def test_detect_functional_score_conflicts_pure_function_no_conflict_when_equal():
    patient_id = uuid.uuid4()
    bp_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    items = [
        _make_item(
            "RNRecertAssessment", "rn_recert_assessments", "RN_RECERT_ASSESSMENT",
            {"pps_score": 40}, patient_id=patient_id, benefit_period_id=bp_id,
            effective_at=now, evidence_id="rn:1",
        ),
        _make_item(
            "F2FEncounter", "f2f_encounters", "F2F_ENCOUNTER",
            {"pps_score_current": 40}, patient_id=patient_id, benefit_period_id=bp_id,
            effective_at=now, evidence_id="f2f:1",
        ),
    ]
    conflicts = detect_functional_score_conflicts(items, tenant_id=uuid.uuid4())
    assert conflicts == []


def test_detect_missing_rn_recert_requirement_pure_function_returns_notice_only():
    patient_id = uuid.uuid4()
    bp_id = uuid.uuid4()
    missing, notices = detect_missing_rn_recert_requirement([], patient_id=patient_id, benefit_period_id=bp_id)
    assert missing == []
    assert len(notices) == 1
    assert notices[0].workflow == "RN_RECERT_ASSESSMENT"
    assert notices[0].status == "POLICY_NOT_CONFIGURED"

    missing_no_scope, notices_no_scope = detect_missing_rn_recert_requirement([], patient_id=patient_id, benefit_period_id=None)
    assert missing_no_scope == []
    assert notices_no_scope == []
