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
from datetime import datetime, timezone
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


class EvidenceOrigin(str, Enum):
    """
    Identifies which acquisition path produced a ClinicalEvidenceItem.

    AUTHORITATIVE_DATABASE is reserved for evidence traced to a persisted,
    identifiable ORM record (source_reference.source_record_id resolves to a
    real row this harvester read directly). LEGACY_ADAPTER is evidence read
    through the legacy duck-typed harvest_clinical_facts() compatibility path,
    which cannot supply record-level provenance -- it must never be labeled
    DOCUMENTED, only UNVERIFIED/MISSING.
    """

    AUTHORITATIVE_DATABASE = "AUTHORITATIVE_DATABASE"
    LEGACY_ADAPTER = "LEGACY_ADAPTER"
    NARRATIVE_EXTRACTION = "NARRATIVE_EXTRACTION"
    CALCULATED = "CALCULATED"
    AI_ESTIMATED = "AI_ESTIMATED"


# =========================================================
# C2. Evidence polarity, conflict, correction/review dimensions
#     (Commit 2D -- kept as separate dimensions from EvidenceStatus rather
#     than overloading it; see evidence_conflict_detection.py for the
#     detection policy that produces ClinicalEvidenceConflict instances)
# =========================================================


class EvidencePolarity(str, Enum):
    """
    Whether a documented item asserts the presence, explicit absence, or an
    unassessed/inapplicable state of a clinical finding. Orthogonal to
    EvidenceStatus (a fact can be DOCUMENTED and EXPLICIT_NEGATIVE at the
    same time -- e.g. a physician documenting "denies dyspnea").

    A polarity of EXPLICIT_NEGATIVE must never be derived from a merely
    absent/None value -- see __post_init__ on ClinicalEvidenceItem, which
    requires full authoritative source identity for EXPLICIT_NEGATIVE just
    as it does for DOCUMENTED.
    """

    POSITIVE = "POSITIVE"
    EXPLICIT_NEGATIVE = "EXPLICIT_NEGATIVE"
    NEUTRAL = "NEUTRAL"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_ASSESSED = "NOT_ASSESSED"


class ConflictType(str, Enum):
    VALUE_DISAGREEMENT = "VALUE_DISAGREEMENT"
    UNIT_INCOMPATIBILITY = "UNIT_INCOMPATIBILITY"
    STATUS_DISAGREEMENT = "STATUS_DISAGREEMENT"
    TEMPORAL_OVERLAP = "TEMPORAL_OVERLAP"
    DUPLICATE_SOURCE_CONFLICT = "DUPLICATE_SOURCE_CONFLICT"
    CORRECTION_CHAIN_CONFLICT = "CORRECTION_CHAIN_CONFLICT"
    PROVENANCE_CONFLICT = "PROVENANCE_CONFLICT"
    # Used only when no approved, versioned comparison-window policy exists
    # to classify the relationship more specifically -- see
    # evidence_conflict_detection.ConflictComparisonPolicy. Never
    # auto-resolved; always human_review_required=True.
    POTENTIAL_CONFLICT = "POTENTIAL_CONFLICT"


class ConflictResolutionStatus(str, Enum):
    UNRESOLVED = "UNRESOLVED"
    RECONCILED = "RECONCILED"
    SUPERSEDED = "SUPERSEDED"
    ENTERED_IN_ERROR = "ENTERED_IN_ERROR"
    NOT_A_CONFLICT = "NOT_A_CONFLICT"


class HumanReviewStatus(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    REQUIRED = "REQUIRED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"


class EvidenceRelationshipType(str, Enum):
    """Correction/supersession/addendum relationship between two evidence
    items or source records. Only used where the source model actually
    carries the backing field(s); FIELD_NOT_AVAILABLE is returned (as a
    plain string, not a fabricated relationship) when it does not."""

    CORRECTS = "CORRECTS"
    SUPERSEDES = "SUPERSEDES"
    ADDENDUM_TO = "ADDENDUM_TO"
    ENTERED_IN_ERROR = "ENTERED_IN_ERROR"
    DUPLICATES = "DUPLICATES"
    CONFIRMS = "CONFIRMS"
    CONTRADICTS = "CONTRADICTS"


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
    # NOTE on naming: the directive's "source_record_id" is this field --
    # source_id already served that role since Commit 1 and is kept (not
    # duplicated) per "do not create duplicate fields that mean the same
    # thing."
    source_id: Optional[str] = None
    # Domain/business record-type label (e.g. "DIAGNOSIS_RECORD"). Distinct
    # from source_model (ORM class name) and source_table (physical table):
    # this describes *what kind of clinical record* it is, independent of
    # how it happens to be persisted.
    source_record_type: Optional[str] = None
    source_field: Optional[str] = None
    source_recorded_at: Optional[datetime] = None
    source_effective_at: Optional[datetime] = None
    source_author_id: Optional[str] = None
    # Whether the source record itself carries a verified authentication/
    # co-signature state (e.g. physician e-signature). Left None -- never
    # fabricated -- when the source model has no such concept.
    authentication_status: Optional[str] = None
    source_version: Optional[str] = None
    # Correction/supersession provenance (Commit 2D will populate these from
    # real correction/addendum records; Commit 2A leaves them None rather
    # than inventing a correction history that does not exist).
    correction_status: Optional[str] = None
    supersedes_record_id: Optional[str] = None
    source_text_span: Optional[str] = None
    source_document_reference: Optional[str] = None
    # Explicit ORM model class name and physical table name for the
    # authoritative-database acquisition path (e.g. "PatientDiagnosis" /
    # "patient_diagnoses"). None for legacy/narrative/calculated evidence
    # that has no single backing table.
    source_model: Optional[str] = None
    source_table: Optional[str] = None
    # Identity fields carried straight from the resolved source row, used to
    # verify (not merely assert) that a DOCUMENTED item's source really
    # belongs to the requesting patient/encounter/benefit period. These are
    # populated by the adapter from the row it actually read -- never from
    # the caller's request parameters -- so a mismatch here indicates the
    # adapter attached evidence to the wrong patient/scope, not merely that
    # the caller asked for a different one.
    source_patient_id: Optional[UUID] = None
    source_encounter_id: Optional[str] = None
    source_benefit_period_id: Optional[UUID] = None

    def __post_init__(self) -> None:
        _require_tz_aware("source_recorded_at", self.source_recorded_at)
        _require_tz_aware("source_effective_at", self.source_effective_at)
        if self.source_field is not None and (
            self.source_table is not None and self.source_field == self.source_table
        ):
            raise ValueError(
                "source_field must not contain a table name "
                f"(source_field == source_table == {self.source_field!r})"
            )


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
    # Defaults to LEGACY_ADAPTER (the conservative assumption) so any caller
    # that does not explicitly assert AUTHORITATIVE_DATABASE provenance is
    # never accidentally treated as authoritative.
    origin: EvidenceOrigin = EvidenceOrigin.LEGACY_ADAPTER
    # Orthogonal to status (see EvidencePolarity). Defaults to POSITIVE --
    # every adapter in this codebase today (Commit 2A/2B/2C) reports a
    # positively-observed value; none of the current source models carry an
    # explicit-denial/normal-finding field, so no adapter sets this to
    # EXPLICIT_NEGATIVE yet.
    polarity: EvidencePolarity = EvidencePolarity.POSITIVE

    def _require_complete_source_identity(self, *, context: str) -> None:
        ref = self.source_reference
        missing = [
            name
            for name, value in (
                ("source_model", ref.source_model),
                ("source_table", ref.source_table),
                ("source_id", ref.source_id),
                ("source_field", ref.source_field),
                ("source_patient_id", ref.source_patient_id),
            )
            if value is None
        ]
        if missing:
            raise ValueError(
                f"{context} requires complete source identity; "
                f"missing {missing} for concept_code={self.concept_code!r}"
            )
        if ref.source_patient_id != self.patient_id:
            raise ValueError(
                f"{context} evidence source_patient_id does not match "
                f"evidence patient_id (source={ref.source_patient_id!r}, "
                f"evidence={self.patient_id!r}) for concept_code={self.concept_code!r}"
            )
        if (
            self.encounter_id is not None
            and ref.source_encounter_id is not None
            and ref.source_encounter_id != self.encounter_id
        ):
            raise ValueError(
                f"{context} evidence source_encounter_id conflicts with "
                f"evidence encounter_id (source={ref.source_encounter_id!r}, "
                f"evidence={self.encounter_id!r}) for concept_code={self.concept_code!r}"
            )
        if (
            self.benefit_period_id is not None
            and ref.source_benefit_period_id is not None
            and ref.source_benefit_period_id != self.benefit_period_id
        ):
            raise ValueError(
                f"{context} evidence source_benefit_period_id conflicts with "
                f"evidence benefit_period_id (source={ref.source_benefit_period_id!r}, "
                f"evidence={self.benefit_period_id!r}) for concept_code={self.concept_code!r}"
            )

    def __post_init__(self) -> None:
        _require_tz_aware("recorded_at", self.recorded_at)
        _require_tz_aware("effective_at", self.effective_at)
        if (
            self.origin != EvidenceOrigin.AUTHORITATIVE_DATABASE
            and self.status == EvidenceStatus.DOCUMENTED
        ):
            raise ValueError(
                "DOCUMENTED status requires origin=AUTHORITATIVE_DATABASE "
                f"(got origin={self.origin.value} for concept_code={self.concept_code!r}); "
                "use UNVERIFIED for non-authoritative evidence."
            )
        if (
            self.origin != EvidenceOrigin.AUTHORITATIVE_DATABASE
            and self.polarity == EvidencePolarity.EXPLICIT_NEGATIVE
        ):
            raise ValueError(
                "EXPLICIT_NEGATIVE polarity requires origin=AUTHORITATIVE_DATABASE "
                f"(got origin={self.origin.value} for concept_code={self.concept_code!r}); "
                "an explicit denial/normal-finding must be traced to a real source record, "
                "never inferred from a merely absent/legacy value."
            )
        if self.status == EvidenceStatus.DOCUMENTED:
            self._require_complete_source_identity(context="DOCUMENTED status")
        if self.polarity == EvidencePolarity.EXPLICIT_NEGATIVE:
            self._require_complete_source_identity(context="EXPLICIT_NEGATIVE polarity")

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return (
            f"ClinicalEvidenceItem(evidence_id={self.evidence_id!r}, "
            f"concept_code={self.concept_code!r}, status={self.status.value})"
        )


# =========================================================
# B2. Structured conflict and missing-requirement contracts (Commit 2D)
# =========================================================


@dataclass(frozen=True)
class ClinicalEvidenceConflict:
    """
    A structured, typed relationship between two or more independently
    sourced DOCUMENTED evidence items that materially disagree.

    Creating a conflict NEVER changes the status of either referenced
    evidence item (both remain DOCUMENTED) and NEVER selects a winning
    value -- winning_evidence_id is populated only after an authorized
    human reviewer resolves the conflict via a future review workflow;
    it is None for every conflict this harvester itself produces.
    """

    conflict_id: str
    patient_id: UUID
    concept_code: str
    evidence_ids: list[str]
    source_references: list[ClinicalSourceReference]
    observed_values: list[Any]
    normalized_values: list[Any]
    conflict_type: ConflictType
    resolution_status: ConflictResolutionStatus
    human_review_required: bool
    created_at: datetime
    encounter_id: Optional[str] = None
    benefit_period_id: Optional[UUID] = None
    instrument: Optional[str] = None
    units: list[Optional[str]] = field(default_factory=list)
    effective_times: list[Optional[datetime]] = field(default_factory=list)
    recorded_times: list[Optional[datetime]] = field(default_factory=list)
    # No approved, versioned clinical-materiality policy exists yet (see
    # evidence_conflict_detection.ConflictComparisonPolicy) -- left as a
    # descriptive string, never a fabricated severity score.
    materiality: str = "UNKNOWN_NO_APPROVED_MATERIALITY_POLICY"
    resolved_by_actor_id: Optional[UUID] = None
    resolved_at: Optional[datetime] = None
    resolution_reason: Optional[str] = None
    winning_evidence_id: Optional[str] = None
    warning_codes: list[str] = field(default_factory=list)
    schema_version: str = CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_tz_aware("created_at", self.created_at)
        _require_tz_aware("resolved_at", self.resolved_at)
        for t in self.effective_times:
            _require_tz_aware("effective_times[]", t)
        for t in self.recorded_times:
            _require_tz_aware("recorded_times[]", t)
        if len(self.evidence_ids) < 2:
            raise ValueError(
                f"ClinicalEvidenceConflict requires at least 2 evidence_ids "
                f"(got {len(self.evidence_ids)}) for concept_code={self.concept_code!r}"
            )
        if self.winning_evidence_id is not None:
            raise ValueError(
                "winning_evidence_id must not be set by automatic conflict "
                "detection -- a conflict is only ever auto-resolved into a "
                "winner by an authorized human reviewer, never by this contract's "
                "producer."
            )


@dataclass(frozen=True)
class MissingEvidenceRequirement:
    """
    A missing WORKFLOW requirement (an expected source record that does not
    exist), kept structurally separate from clinical observations. Must
    never be represented as a fake ClinicalEvidenceItem -- a missing RN
    recertification assessment is an operational gap, not a clinical
    finding of "no assessment performed" (which would itself require a
    real documented source to assert).
    """

    requirement_id: str
    patient_id: UUID
    requirement_code: str
    expected_source_type: str
    reason_required: str
    status: str
    detected_at: datetime
    human_review_required: bool
    encounter_id: Optional[str] = None
    benefit_period_id: Optional[UUID] = None
    expected_field: Optional[str] = None
    schema_version: str = CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_tz_aware("detected_at", self.detected_at)


@dataclass(frozen=True)
class ClinicalEvidenceBundle:
    """Ordered, deduplicated collection of evidence items for one patient."""

    patient_id: UUID
    items: list[ClinicalEvidenceItem] = field(default_factory=list)
    conflicts: list[ClinicalEvidenceConflict] = field(default_factory=list)
    missing_requirements: list[MissingEvidenceRequirement] = field(default_factory=list)
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

    def by_source(self, source_model: str) -> list[ClinicalEvidenceItem]:
        return [item for item in self.items if item.source_reference.source_model == source_model]

    def chronological(self) -> list[ClinicalEvidenceItem]:
        """
        Canonical clinical chronology: effective_at ascending (nulls last),
        recorded_at ascending (nulls last), then source_model/source_id/
        source_field/evidence_id as a purely-for-determinism tie-break --
        never used to establish prior-vs-current, only to make repeated
        calls byte-identical when every real timestamp ties.
        """

        def key(item: ClinicalEvidenceItem):
            ref = item.source_reference
            _min = datetime.min.replace(tzinfo=timezone.utc)
            return (
                item.effective_at is None,
                item.effective_at or _min,
                item.recorded_at is None,
                item.recorded_at or _min,
                ref.source_model or "",
                ref.source_id or "",
                ref.source_field or "",
                item.evidence_id,
            )

        return sorted(self.items, key=key)

    def latest_effective(self, concept_code: str) -> Optional[ClinicalEvidenceItem]:
        """
        Returns the item with the greatest effective_at for a concept, or
        None if no item has an effective_at. Does NOT imply this is a
        "winning"/authoritative value when multiple items share the same
        (or no) effective_at -- callers needing that distinction must
        consult bundle.conflicts.
        """
        candidates = [item for item in self.by_concept_code(concept_code) if item.effective_at is not None]
        if not candidates:
            return None
        return max(candidates, key=lambda item: item.effective_at)

    def unresolved_conflicts(self) -> list[ClinicalEvidenceConflict]:
        return [
            c for c in self.conflicts
            if c.resolution_status == ConflictResolutionStatus.UNRESOLVED
        ]


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
