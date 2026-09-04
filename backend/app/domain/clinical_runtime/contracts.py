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
        if self.status == EvidenceStatus.DOCUMENTED:
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
                    "DOCUMENTED status requires complete source identity; "
                    f"missing {missing} for concept_code={self.concept_code!r}"
                )
            if ref.source_patient_id != self.patient_id:
                raise ValueError(
                    "DOCUMENTED evidence source_patient_id does not match "
                    f"evidence patient_id (source={ref.source_patient_id!r}, "
                    f"evidence={self.patient_id!r}) for concept_code={self.concept_code!r}"
                )
            if (
                self.encounter_id is not None
                and ref.source_encounter_id is not None
                and ref.source_encounter_id != self.encounter_id
            ):
                raise ValueError(
                    "DOCUMENTED evidence source_encounter_id conflicts with "
                    f"evidence encounter_id (source={ref.source_encounter_id!r}, "
                    f"evidence={self.encounter_id!r}) for concept_code={self.concept_code!r}"
                )
            if (
                self.benefit_period_id is not None
                and ref.source_benefit_period_id is not None
                and ref.source_benefit_period_id != self.benefit_period_id
            ):
                raise ValueError(
                    "DOCUMENTED evidence source_benefit_period_id conflicts with "
                    f"evidence benefit_period_id (source={ref.source_benefit_period_id!r}, "
                    f"evidence={self.benefit_period_id!r}) for concept_code={self.concept_code!r}"
                )

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
