# app/services/eligibility/evidence_conflict_detection.py
"""
Commit 2D: structured conflict and missing-workflow-requirement detection
over an assembled ClinicalEvidenceHarvester items list.

This module NEVER mutates or reclassifies an input ClinicalEvidenceItem's
status/polarity -- every DOCUMENTED item stays DOCUMENTED regardless of any
conflict found (see ClinicalEvidenceConflict's docstring). It also never
selects a "winning" value between disagreeing sources; conflicts are always
created with resolution_status=UNRESOLVED and winning_evidence_id=None.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from app.domain.clinical_runtime.contracts import (
    ClinicalEvidenceConflict,
    ClinicalEvidenceItem,
    ConflictResolutionStatus,
    ConflictType,
    MissingEvidenceRequirement,
)


class ConflictComparisonPolicy:
    """
    Versioned, explicit policy for whether two effective timestamps fall
    within the "same clinically relevant timeframe" for conflict detection.

    version="unapproved-default-v1": no clinical/product-approved
    comparison window (e.g. "within N days counts as the same assessment
    cycle") has been defined for this repository yet. The only safe,
    zero-arbitrary-threshold rule this default applies is EXACT same-day
    equality of effective_at -- an identity comparison, not a magnitude
    threshold. Any other relationship (the effective dates genuinely
    differ, or either side is missing an effective_at) is left
    unclassified as either "trend" or "same-period conflict"; the caller
    treats that as ConflictType.POTENTIAL_CONFLICT with
    human_review_required=True rather than auto-resolving it either way.

    Replace this class (bump `version`) once an approved clinical policy
    defines a real comparison window -- do not hardcode a number of
    hours/days here without that approval.
    """

    version = "unapproved-default-v1"

    def classify(self, a: Optional[datetime], b: Optional[datetime]) -> str:
        """Returns one of "same_period", "different_period", "unknown"."""
        if a is None or b is None:
            return "unknown"
        if a.date() == b.date():
            return "same_period"
        return "different_period"


# Instrument -> list of (source_model, normalized_value key) pairs that are
# genuinely the same measured clinical concept across independently-sourced
# adapters. Deliberately explicit and narrow -- only pairs verified to mean
# the same thing are listed. F2FEncounter.pps_score_previous is that
# encounter's OWN recorded historical baseline (not a new independent
# observation), so it is never compared here -- only *_current values are.
FUNCTIONAL_SCORE_FIELD_MAP: dict[str, list[tuple[str, str]]] = {
    "PPS": [("RNRecertAssessment", "pps_score"), ("F2FEncounter", "pps_score_current")],
    "KPS": [("RNRecertAssessment", "kps_score"), ("F2FEncounter", "kps_score")],
    "FAST": [("RNRecertAssessment", "fast_stage"), ("F2FEncounter", "fast_score")],
    "NYHA": [("RNRecertAssessment", "nyha_class"), ("F2FEncounter", "nyha_class")],
    "ADL": [("RNRecertAssessment", "adl_level"), ("F2FEncounter", "adl_dependency_level")],
    # ECOG exists only on F2FEncounter today -- RNRecertAssessment has no
    # ecog_score_* field (rn_recert_assessment.py). Cross-source comparison
    # is not possible; this is FIELD_NOT_AVAILABLE on the RN side, not
    # fabricated. Left with a single entry so no pairwise comparison is
    # ever attempted for ECOG.
    "ECOG": [("F2FEncounter", "ecog_score_current")],
}


def detect_functional_score_conflicts(
    items: list[ClinicalEvidenceItem],
    *,
    policy: Optional[ConflictComparisonPolicy] = None,
    now: Optional[datetime] = None,
) -> list[ClinicalEvidenceConflict]:
    """
    Compares functional-assessment scores across independently-sourced
    DOCUMENTED items (today: RNRecertAssessment vs F2FEncounter) that share
    the same benefit_period_id, and produces a structured
    ClinicalEvidenceConflict wherever the values genuinely differ and the
    comparison policy does not classify the relationship as a trend across
    different effective periods.
    """
    policy = policy or ConflictComparisonPolicy()
    now = now or datetime.now(timezone.utc)
    conflicts: list[ClinicalEvidenceConflict] = []

    for instrument, field_map in FUNCTIONAL_SCORE_FIELD_MAP.items():
        if len(field_map) < 2:
            continue  # only one source model has this field today (e.g. ECOG).

        by_bp: dict[Optional[UUID], list[tuple[str, ClinicalEvidenceItem, object]]] = {}
        for source_model, value_field in field_map:
            for item in items:
                if item.source_reference.source_model != source_model:
                    continue
                if item.normalized_value is None or value_field not in item.normalized_value:
                    continue
                value = item.normalized_value[value_field]
                if value is None:
                    continue
                by_bp.setdefault(item.benefit_period_id, []).append((source_model, item, value))

        for bp_id, entries in by_bp.items():
            for i in range(len(entries)):
                for j in range(i + 1, len(entries)):
                    model_a, item_a, value_a = entries[i]
                    model_b, item_b, value_b = entries[j]
                    if model_a == model_b:
                        continue  # independent sourcing required.
                    if value_a == value_b:
                        continue  # identical value: not a conflict.

                    relation = policy.classify(item_a.effective_at, item_b.effective_at)
                    if relation == "different_period":
                        # A trend across meaningfully different effective
                        # times, not a conflict -- preserved via ordering,
                        # not flagged.
                        continue

                    conflict_type = (
                        ConflictType.VALUE_DISAGREEMENT
                        if relation == "same_period"
                        else ConflictType.POTENTIAL_CONFLICT
                    )
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
                            benefit_period_id=bp_id,
                            instrument=instrument,
                            units=[item_a.unit, item_b.unit],
                            effective_times=[item_a.effective_at, item_b.effective_at],
                            recorded_times=[item_a.recorded_at, item_b.recorded_at],
                            warning_codes=[f"{policy.version}:{relation}"],
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
) -> list[MissingEvidenceRequirement]:
    """
    Flags a missing RN recertification assessment for the requested benefit
    period as a MissingEvidenceRequirement (an operational workflow gap),
    never as a fabricated ClinicalEvidenceItem. Only produced when the
    caller scoped the harvest to a specific benefit_period_id -- without
    that scope there is no single expected record to be missing.
    """
    if benefit_period_id is None:
        return []
    now = now or datetime.now(timezone.utc)
    has_assessment = any(
        item.source_reference.source_model == "RNRecertAssessment"
        and item.benefit_period_id == benefit_period_id
        for item in items
    )
    if has_assessment:
        return []
    return [
        MissingEvidenceRequirement(
            requirement_id=str(uuid4()),
            patient_id=patient_id,
            requirement_code="RN_RECERT_ASSESSMENT_MISSING",
            expected_source_type="RNRecertAssessment",
            reason_required=(
                "A benefit-period-scoped harvest expects at least one RN "
                "recertification assessment for that benefit period."
            ),
            status="MISSING",
            detected_at=now,
            human_review_required=True,
            benefit_period_id=benefit_period_id,
        )
    ]
