# app/domain/clinical_runtime/contracts.py
"""
Shared typed runtime contracts for the production clinical runtime pipeline:

    create_patient_from_hnp()
        -> Clinical input normalization
        -> Evidence Harvester
        -> Evidence provenance and status classification
        -> Ontology resolution
        -> Disease-family resolution
        -> Functional Assessment Service (PPS/KPS/NYHA/ECOG/FAST/ADL)
        -> Terminal Status Framework
        -> Recertification Framework
        -> Human-reviewable result
        -> Persisted audit record

These dataclasses are the ONLY typed objects that may cross a major pipeline
stage boundary. Untyped dictionaries must not be passed between stages -- a
stage may use dictionaries internally, but its public input/output must be one
of the contracts defined here (or a stage-specific contract that itself is
built from these primitives).

Every contract preserves:
    - provenance (source_reference on the evidence item / result)
    - fact-status semantics (see EvidenceStatus) so that a clinician-documented
      value is never silently conflated with an AI-estimated or calculated one
    - determinism (no wall-clock/random values inside a contract's *content*;
      timestamps are inputs supplied by the caller, not generated implicitly)

This module intentionally has zero database/session dependencies so it can be
imported by every runtime stage, every test, and (later) any API schema layer
without creating import cycles.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID


# =========================================================
# C. Evidence status
# =========================================================


class EvidenceStatus(str, Enum):
    """
    Fact-status semantics for a single clinical evidence item or a derived
    functional-assessment/terminal-status/recertification result.

    DOCUMENTED and AI_ESTIMATED must never be combined or relabeled into one
    another. A provenance failure must resolve to MISSING/UNVERIFIED, never to
    an apparently-valid DOCUMENTED or CALCULATED value.
    """

    DOCUMENTED = "DOCUMENTED"
    AI_EXTRACTED = "AI_EXTRACTED"
    AI_ESTIMATED = "AI_ESTIMATED"
    CALCULATED = "CALCULATED"
    INFERRED = "INFERRED"
    CONFLICTING = "CONFLICTING"
    MISSING = "MISSING"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNVERIFIED = "UNVERIFIED"


# =========================================================
# Shared runtime error codes (Evidence Harvester)
# =========================================================


class EvidenceErrorCode(str, Enum):
    EVIDENCE_SOURCE_UNAVAILABLE = "EVIDENCE_SOURCE_UNAVAILABLE"
    EVIDENCE_SOURCE_UNAUTHORIZED = "EVIDENCE_SOURCE_UNAUTHORIZED"
    EVIDENCE_NORMALIZATION_FAILED = "EVIDENCE_NORMALIZATION_FAILED"
    EVIDENCE_CONFLICT = "EVIDENCE_CONFLICT"
    EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"
    EVIDENCE_PROVENANCE_MISSING = "EVIDENCE_PROVENANCE_MISSING"


class RuntimeStageStatus(str, Enum):
    """Allowed values for RuntimeTrace.status."""

    STARTED = "STARTED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


# Current contract schema version. Bump when a contract's persisted/serialized
# shape changes in a way that downstream consumers (audit records, API
# responses) need to distinguish.
CONTRACT_SCHEMA_VERSION = "v1"


def _require_tz_aware(field_name: str, value: Optional[datetime]) -> None:
    """
    Enforce that any timestamp carried on a runtime contract is timezone-aware.
    Naive datetimes are a common source of silent, non-deterministic bugs when
    comparing evidence recorded across UTC/local boundaries.
    """

    if value is not None and value.tzinfo is None:
        raise ValueError(
            f"{field_name} must be a timezone-aware datetime (got naive datetime {value!r})"
        )


# =========================================================
# A. Clinical source reference
# =========================================================


@dataclass(frozen=True)
class ClinicalSourceReference:
    source_type: str
    source_id: Optional[str] = None
    source_record_type: Optional[str] = None
    source_field: Optional[str] = None
    source_recorded_at: Optional[datetime] = None
    source_author_id: Optional[str] = None
    source_version: Optional[str] = None
    source_text_span: Optional[str] = None
    source_document_reference: Optional[str] = None

    def __post_init__(self) -> None:
        _require_tz_aware("source_recorded_at", self.source_recorded_at)


# =========================================================
# B. Clinical evidence item
# =========================================================


@dataclass(frozen=True, repr=False)
class ClinicalEvidenceItem:
    """
    A single clinical fact with full provenance.

    repr is intentionally overridden: the default dataclass repr would print
    observed_value/normalized_value (clinical data that may be sensitive) into
    any log line or exception traceback that captures this object. The custom
    repr below identifies the item by evidence_id/concept_code/status only.
    """

    evidence_id: str
    patient_id: UUID
    concept_code: str
    canonical_name: str
    status: EvidenceStatus
    source_reference: ClinicalSourceReference
    encounter_id: Optional[str] = None
    benefit_period_id: Optional[UUID] = None
    observed_value: Optional[Any] = None
    normalized_value: Optional[Any] = None
    unit: Optional[str] = None
    recorded_at: Optional[datetime] = None
    effective_at: Optional[datetime] = None
    confidence: Optional[float] = None
    extraction_method: Optional[str] = None
    ontology_reference: Optional["OntologyResolutionResult"] = None
    warnings: list[str] = field(default_factory=list)
    schema_version: str = CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_tz_aware("recorded_at", self.recorded_at)
        _require_tz_aware("effective_at", self.effective_at)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return (
            f"ClinicalEvidenceItem(evidence_id={self.evidence_id!r}, "
            f"concept_code={self.concept_code!r}, status={self.status.value})"
        )


@dataclass(frozen=True)
class ClinicalEvidenceBundle:
    """Ordered, deduplicated collection of evidence items for one patient."""

    patient_id: UUID
    items: list[ClinicalEvidenceItem] = field(default_factory=list)
    encounter_id: Optional[str] = None
    benefit_period_id: Optional[UUID] = None
    generated_at: Optional[datetime] = None
    warnings: list[str] = field(default_factory=list)
    errors: list[EvidenceErrorCode] = field(default_factory=list)
    schema_version: str = CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_tz_aware("generated_at", self.generated_at)

    def by_concept_code(self, concept_code: str) -> list[ClinicalEvidenceItem]:
        return [item for item in self.items if item.concept_code == concept_code]


# =========================================================
# Ontology resolution result (referenced by ClinicalEvidenceItem)
# =========================================================


@dataclass(frozen=True)
class OntologyResolutionResult:
    ontology_id: Optional[str] = None
    concept_id: Optional[str] = None
    canonical_name: Optional[str] = None
    matched_alias: Optional[str] = None
    disease_family: Optional[str] = None
    variant: Optional[str] = None
    relationship_type: Optional[str] = None
    source_classification: Optional[str] = None
    source_reference: Optional[ClinicalSourceReference] = None
    ontology_version: Optional[str] = None
    match_method: Optional[str] = None
    match_confidence: Optional[float] = None
    ambiguity: bool = False
    warnings: list[str] = field(default_factory=list)


# =========================================================
# D. Functional assessment result
# =========================================================


@dataclass(frozen=True)
class FunctionalAssessmentResult:
    instrument: str
    value: Optional[Any]
    normalized_value: Optional[Any]
    status: EvidenceStatus
    complete: bool
    components_used: list[str] = field(default_factory=list)
    components_missing: list[str] = field(default_factory=list)
    calculation_version: Optional[str] = None
    ontology_version: Optional[str] = None
    evidence_ids: list[str] = field(default_factory=list)
    source_references: list[ClinicalSourceReference] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    calculated_at: Optional[datetime] = None
    calculated_by: Optional[str] = None
    schema_version: str = CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_tz_aware("calculated_at", self.calculated_at)


# =========================================================
# E. Terminal-status result
# =========================================================


@dataclass(frozen=True)
class TerminalStatusResult:
    patient_id: UUID
    disease_family: str
    framework_version: str
    result_status: EvidenceStatus
    encounter_id: Optional[str] = None
    benefit_period_id: Optional[UUID] = None
    criteria_evaluated: list[str] = field(default_factory=list)
    criteria_supported: list[str] = field(default_factory=list)
    criteria_not_supported: list[str] = field(default_factory=list)
    criteria_unknown: list[str] = field(default_factory=list)
    functional_assessments: list[FunctionalAssessmentResult] = field(default_factory=list)
    supporting_evidence_ids: list[str] = field(default_factory=list)
    contradicting_evidence_ids: list[str] = field(default_factory=list)
    source_references: list[ClinicalSourceReference] = field(default_factory=list)
    human_review_required: bool = True
    warnings: list[str] = field(default_factory=list)
    evaluated_at: Optional[datetime] = None
    schema_version: str = CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_tz_aware("evaluated_at", self.evaluated_at)


# =========================================================
# F. Recertification result
# =========================================================


@dataclass(frozen=True)
class RecertificationResult:
    benefit_period_id: UUID
    framework_version: str
    current_evidence: ClinicalEvidenceBundle
    terminal_status_result: Optional[TerminalStatusResult] = None
    prior_certification_reference: Optional[str] = None
    comparative_trends: dict[str, Any] = field(default_factory=dict)
    stability_or_improvement: Optional[str] = None
    continued_decline_support: Optional[bool] = None
    missing_information: list[str] = field(default_factory=list)
    human_review_required: bool = True
    generated_at: Optional[datetime] = None
    schema_version: str = CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_tz_aware("generated_at", self.generated_at)


# =========================================================
# G. Runtime trace
# =========================================================


@dataclass(frozen=True)
class RuntimeTrace:
    trace_id: str
    patient_id: UUID
    pipeline_version: str
    stage: str
    status: RuntimeStageStatus
    started_at: datetime
    encounter_id: Optional[str] = None
    benefit_period_id: Optional[UUID] = None
    completed_at: Optional[datetime] = None
    input_reference: Optional[str] = None
    output_reference: Optional[str] = None
    error_code: Optional[str] = None
    warning_codes: list[str] = field(default_factory=list)
    actor_type: str = "SYSTEM"
    schema_version: str = CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_tz_aware("started_at", self.started_at)
        _require_tz_aware("completed_at", self.completed_at)
