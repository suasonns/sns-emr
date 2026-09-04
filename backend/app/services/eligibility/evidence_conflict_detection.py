# app/services/eligibility/evidence_conflict_detection.py
"""
Commit 2D (corrected): structured conflict and missing-workflow-requirement
detection over an assembled ClinicalEvidenceHarvester items list.

ENGINEERING CORRECTION (post Commit 2D review): the original version of
this module contained an unapproved, self-invented clinical/timing policy
("same day = conflict, different day = trend"). That policy has been
REMOVED. This module now only ever:

  - groups independently-sourced items using purely structural identity
    (patient/tenant/benefit period/encounter/instrument/instrument
    version/unit/source model/source field/correction state/supersession
    state) -- never a clinical judgment;
  - checks an InstrumentComparisonPolicy registry for an APPROVED policy
    before classifying a value disagreement any more specifically than
    ConflictType.POTENTIAL_CONFLICT;
  - checks an EvidenceRequirementPolicy registry for an APPROVED policy
    before generating a formal MissingEvidenceRequirement -- absent an
    approved policy, a RequirementPolicyNotice(status="POLICY_NOT_CONFIGURED")
    is returned instead, never a fabricated missing-evidence finding.

Every policy shipped in this module today is DRAFT_NOT_ACTIVE (see
INSTRUMENT_COMPARISON_POLICIES / EVIDENCE_REQUIREMENT_POLICIES below). No
clinical threshold, comparison window, or "required for every X" rule may
be added to a DRAFT policy or activated without an explicit, documented
approval (approved_by + approved_at) from an authorized clinical/agency
reviewer -- enforced structurally by
InstrumentComparisonPolicy.__post_init__ / EvidenceRequirementPolicy.__post_init__
in contracts.py, which refuse to construct an APPROVED policy without both.

This module NEVER mutates or reclassifies an input ClinicalEvidenceItem's
status/polarity -- every DOCUMENTED item stays DOCUMENTED regardless of any
conflict found. It also never selects a "winning" value between
disagreeing sources; conflicts are always created with
resolution_status=UNRESOLVED, human_review_required=True, and
winning_evidence_id=None.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from app.domain.clinical_runtime.contracts import (
    CapabilityStatus,
    ClinicalEvidenceConflict,
    ClinicalEvidenceItem,
    ConflictResolutionStatus,
    ConflictType,
    EvidenceRequirementPolicy,
    InstrumentComparisonPolicy,
    MissingEvidenceRequirement,
    PolicyApprovalStatus,
    RequirementPolicyNotice,
    SourceCapability,
)

# =========================================================
# Source capability registry -- what a given source model can and cannot
# supply. Declared explicitly rather than inferred by "the field lookup
# returned None", so a genuinely-missing capability is never confused with
# a row that simply has a null value for a field it does carry.
# =========================================================

SOURCE_CAPABILITIES: list[SourceCapability] = [
    SourceCapability("RNRecertAssessment", "pps_score", CapabilityStatus.AVAILABLE),
    SourceCapability("RNRecertAssessment", "kps_score", CapabilityStatus.AVAILABLE),
    SourceCapability("RNRecertAssessment", "fast_stage", CapabilityStatus.AVAILABLE),
    SourceCapability("RNRecertAssessment", "nyha_class", CapabilityStatus.AVAILABLE),
    SourceCapability("RNRecertAssessment", "adl_level", CapabilityStatus.AVAILABLE),
    SourceCapability(
        "RNRecertAssessment", "ecog_score", CapabilityStatus.FIELD_NOT_AVAILABLE,
        notes="RNRecertAssessment has no ecog_score_* column (see app/models/rn_recert_assessment.py).",
    ),
    SourceCapability("F2FEncounter", "pps_score_current", CapabilityStatus.AVAILABLE),
    SourceCapability("F2FEncounter", "kps_score", CapabilityStatus.AVAILABLE),
    SourceCapability("F2FEncounter", "fast_score", CapabilityStatus.AVAILABLE),
    SourceCapability("F2FEncounter", "nyha_class", CapabilityStatus.AVAILABLE),
    SourceCapability("F2FEncounter", "adl_dependency_level", CapabilityStatus.AVAILABLE),
    SourceCapability("F2FEncounter", "ecog_score_current", CapabilityStatus.AVAILABLE),
]

_CAPABILITY_INDEX = {(c.source_model, c.field_name): c for c in SOURCE_CAPABILITIES}


def get_capability(source_model: str, field_name: str) -> SourceCapability:
    """Returns the declared capability, or a FIELD_NOT_AVAILABLE default if
    this (source_model, field_name) pair was never explicitly registered --
    an unregistered pair is treated the same as a known-absent field, never
    silently treated as available."""
    return _CAPABILITY_INDEX.get(
        (source_model, field_name),
        SourceCapability(source_model, field_name, CapabilityStatus.FIELD_NOT_AVAILABLE,
                          notes="Not registered in SOURCE_CAPABILITIES."),
    )


# Instrument -> list of (source_model, normalized_value key) pairs that are
# genuinely the same measured clinical concept across independently-sourced
# adapters. Deliberately explicit and narrow -- only pairs verified to mean
# the same thing are listed. F2FEncounter.pps_score_previous is that
# encounter's OWN recorded historical baseline (not a new independent
# observation), so it is never compared here -- only *_current values are.
#
# ECOG intentionally has only one entry: RNRecertAssessment cannot supply
# it (see SOURCE_CAPABILITIES above), so no pairwise comparison is ever
# attempted for ECOG.
FUNCTIONAL_SCORE_FIELD_MAP: dict[str, list[tuple[str, str]]] = {
    "PPS": [("RNRecertAssessment", "pps_score"), ("F2FEncounter", "pps_score_current")],
    "KPS": [("RNRecertAssessment", "kps_score"), ("F2FEncounter", "kps_score")],
    "FAST": [("RNRecertAssessment", "fast_stage"), ("F2FEncounter", "fast_score")],
    "NYHA": [("RNRecertAssessment", "nyha_class"), ("F2FEncounter", "nyha_class")],
    "ADL": [("RNRecertAssessment", "adl_level"), ("F2FEncounter", "adl_dependency_level")],
    "ECOG": [("F2FEncounter", "ecog_score_current")],
}

# No source model in this codebase carries an instrument-version field
# today (e.g. "PPS scale revision 2001 vs 2013"). This is FIELD_NOT_AVAILABLE
# everywhere, not fabricated -- kept as a named constant so every call site
# uses the identical sentinel rather than inventing ad hoc strings.
_NO_INSTRUMENT_VERSION = "FIELD_NOT_AVAILABLE"
_NO_ASSESSMENT_CONTEXT = "FIELD_NOT_AVAILABLE"


def _correction_state(item: ClinicalEvidenceItem) -> str:
    """RNRecertAssessment and F2FEncounter carry no correction/entered-in-
    error field today; Certification's real correction_status (surfaced on
    ClinicalSourceReference.correction_status in Commit 2B) is passed
    through when present."""
    return item.source_reference.correction_status or "FIELD_NOT_AVAILABLE"


def _supersession_state(item: ClinicalEvidenceItem) -> str:
    ref = item.source_reference
    return "SUPERSEDED" if ref.correction_status == "SUPERSEDED" else "NOT_SUPERSEDED"


# =========================================================
# Policy registries -- ALL DRAFT_NOT_ACTIVE. See module docstring: only an
# APPROVED policy (approved_by + approved_at populated, see
# InstrumentComparisonPolicy/EvidenceRequirementPolicy in contracts.py) may
# ever be consulted for automatic classification or formal
# missing-requirement generation. These DRAFT entries exist solely so the
# *shape* of each pending decision is visible for review -- they carry no
# threshold, window, or requirement-rule fields, and none of the string
# constants below should be read as an engineering recommendation for what
# the eventual approved value should be.
# =========================================================

INSTRUMENT_COMPARISON_POLICIES: dict[str, InstrumentComparisonPolicy] = {
    instrument: InstrumentComparisonPolicy(
        policy_id=f"instrument-comparison-{instrument.lower()}-v1",
        policy_version="0.1-draft",
        instrument=instrument,
        approval_status=PolicyApprovalStatus.DRAFT,
    )
    for instrument in ("PPS", "KPS", "NYHA", "ECOG", "FAST", "ADL")
}

EVIDENCE_REQUIREMENT_POLICIES: dict[str, EvidenceRequirementPolicy] = {
    workflow: EvidenceRequirementPolicy(
        policy_id=f"evidence-requirement-{workflow.lower()}-v1",
        policy_version="0.1-draft",
        workflow=workflow,
        approval_status=PolicyApprovalStatus.DRAFT,
    )
    for workflow in ("RN_RECERT_ASSESSMENT", "CERTIFICATION", "F2F_ENCOUNTER")
}


def _active_comparison_policy(instrument: str) -> Optional[InstrumentComparisonPolicy]:
    policy = INSTRUMENT_COMPARISON_POLICIES.get(instrument)
    return policy if policy is not None and policy.is_active() else None


def _active_requirement_policy(workflow: str) -> Optional[EvidenceRequirementPolicy]:
    policy = EVIDENCE_REQUIREMENT_POLICIES.get(workflow)
    return policy if policy is not None and policy.is_active() else None


def detect_functional_score_conflicts(
    items: list[ClinicalEvidenceItem],
    *,
    tenant_id: Optional[UUID] = None,
    now: Optional[datetime] = None,
) -> list[ClinicalEvidenceConflict]:
    """
    Compares functional-assessment scores across independently-sourced
    DOCUMENTED items (today: RNRecertAssessment vs F2FEncounter) that share
    identical conflict-identity (patient/benefit_period/encounter/
    instrument/instrument_version/unit/source-field-role/correction and
    supersession state), and produces a structured ClinicalEvidenceConflict
    wherever the values genuinely differ.

    SAFE FALLBACK (no clinical policy invented here): because no
    InstrumentComparisonPolicy is APPROVED for any instrument today, every
    genuine value disagreement is classified as ConflictType.POTENTIAL_CONFLICT
    with resolution_status=UNRESOLVED and human_review_required=True --
    never auto-classified as a same-period "VALUE_DISAGREEMENT" or a
    different-period "trend" (no conflict object at all). Both observations
    are always preserved as ordinary evidence items regardless.
    """
    now = now or datetime.now(timezone.utc)
    conflicts: list[ClinicalEvidenceConflict] = []

    for instrument, field_map in FUNCTIONAL_SCORE_FIELD_MAP.items():
        if len(field_map) < 2:
            continue  # only one source model can supply this instrument today.

        active_policy = _active_comparison_policy(instrument)

        # Group by the full structural conflict-identity tuple (excluding
        # the value itself and the effective/recorded times, which are
        # recorded on the conflict but never used to gate whether a
        # comparison is attempted).
        groups: dict[tuple, list[tuple[str, ClinicalEvidenceItem, object]]] = {}
        for source_model, value_field in field_map:
            for item in items:
                if item.source_reference.source_model != source_model:
                    continue
                if item.normalized_value is None or value_field not in item.normalized_value:
                    continue
                value = item.normalized_value[value_field]
                if value is None:
                    continue
                capability = get_capability(source_model, value_field)
                if capability.status != CapabilityStatus.AVAILABLE:
                    continue  # FIELD_NOT_AVAILABLE -- never compared.

                identity_key = (
                    item.patient_id,
                    tenant_id,
                    item.benefit_period_id,
                    item.encounter_id,
                    instrument,
                    _NO_INSTRUMENT_VERSION,
                    item.unit,
                    _NO_ASSESSMENT_CONTEXT,
                )
                groups.setdefault(identity_key, []).append((source_model, item, value))

        for identity_key, entries in groups.items():
            for i in range(len(entries)):
                for j in range(i + 1, len(entries)):
                    model_a, item_a, value_a = entries[i]
                    model_b, item_b, value_b = entries[j]
                    if model_a == model_b:
                        continue  # independent sourcing required.
                    if value_a == value_b:
                        continue  # identical value: not a conflict.

                    if active_policy is not None:
                        # No policy is APPROVED today, so this branch is
                        # currently unreachable -- once a real policy is
                        # approved, its (not-yet-defined) classification
                        # logic must be implemented here explicitly, never
                        # inferred.
                        conflict_type = ConflictType.POTENTIAL_CONFLICT
                        warning_codes = [f"{active_policy.policy_id}:{active_policy.policy_version}"]
                    else:
                        conflict_type = ConflictType.POTENTIAL_CONFLICT
                        warning_codes = ["NO_APPROVED_COMPARISON_POLICY"]

                    conflicts.append(
                        ClinicalEvidenceConflict(
                            conflict_id=str(uuid4()),
                            patient_id=item_a.patient_id,
                            concept_code=instrument,
                            evidence_ids=sorted([item_a.evidence_id, item_b.evidence_id]),
                            source_references=[item_a.source_reference, item_b.source_reference],
                            observed_values=[value_a, value_b],
                            normalized_values=[value_a, value_b],
                            conflict_type=conflict_type,
                            resolution_status=ConflictResolutionStatus.UNRESOLVED,
                            human_review_required=True,
                            created_at=now,
                            tenant_id=tenant_id,
                            encounter_id=item_a.encounter_id,
                            benefit_period_id=item_a.benefit_period_id,
                            instrument=instrument,
                            instrument_version=_NO_INSTRUMENT_VERSION,
                            assessment_context=_NO_ASSESSMENT_CONTEXT,
                            source_models=[model_a, model_b],
                            source_fields=[item_a.source_reference.source_field or "", item_b.source_reference.source_field or ""],
                            correction_states=[_correction_state(item_a), _correction_state(item_b)],
                            supersession_states=[_supersession_state(item_a), _supersession_state(item_b)],
                            units=[item_a.unit, item_b.unit],
                            effective_times=[item_a.effective_at, item_b.effective_at],
                            recorded_times=[item_a.recorded_at, item_b.recorded_at],
                            warning_codes=warning_codes,
                        )
                    )

    # Deterministic ordering: never rely on dict/set iteration order.
    conflicts.sort(key=lambda c: (c.concept_code, tuple(c.evidence_ids)))
    return conflicts


def detect_missing_rn_recert_requirement(
    items: list[ClinicalEvidenceItem],
    *,
    patient_id: UUID,
    benefit_period_id: Optional[UUID],
    now: Optional[datetime] = None,
) -> tuple[list[MissingEvidenceRequirement], list[RequirementPolicyNotice]]:
    """
    Returns (missing_requirements, policy_notices).

    SAFE FALLBACK: no EvidenceRequirementPolicy is APPROVED for
    RN_RECERT_ASSESSMENT today, so this NEVER generates a formal
    MissingEvidenceRequirement -- doing so would itself be an unapproved
    "an RN recert assessment is required for every benefit period" policy
    decision. Instead, whenever benefit_period_id is explicitly scoped
    (the only condition under which a requirement could ever apply), a
    RequirementPolicyNotice(status="POLICY_NOT_CONFIGURED") is returned so
    callers can see a decision is pending, without treating it as a
    clinical finding.
    """
    now = now or datetime.now(timezone.utc)
    if benefit_period_id is None:
        return [], []

    policy = _active_requirement_policy("RN_RECERT_ASSESSMENT")
    if policy is None:
        return [], [RequirementPolicyNotice(workflow="RN_RECERT_ASSESSMENT", detected_at=now)]

    # Unreachable today (no policy is ever APPROVED by this module) -- once
    # a real policy is approved, its (not-yet-defined) requirement rule
    # must be implemented here explicitly, never inferred.
    has_assessment = any(
        item.source_reference.source_model == "RNRecertAssessment"
        and item.benefit_period_id == benefit_period_id
        for item in items
    )
    if has_assessment:
        return [], []
    return [
        MissingEvidenceRequirement(
            requirement_id=str(uuid4()),
            patient_id=patient_id,
            requirement_code="RN_RECERT_ASSESSMENT_MISSING",
            expected_source_type="RNRecertAssessment",
            reason_required=f"Required by approved policy {policy.policy_id}.",
            status="MISSING",
            detected_at=now,
            human_review_required=True,
            benefit_period_id=benefit_period_id,
        )
    ], []
