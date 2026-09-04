# tests/clinical_runtime/test_contracts.py
"""
Unit tests for app.domain.clinical_runtime.contracts (Commit 1).

These tests verify only that the shared runtime contracts:
  - construct correctly with required fields
  - preserve provenance (source_reference) end-to-end
  - keep DOCUMENTED and AI_ESTIMATED evidence status distinct
  - are immutable (frozen dataclasses)
  - support lookup helpers used by later pipeline stages

They intentionally do not exercise any database or service code -- this
module has zero DB dependencies by design.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.domain.clinical_runtime.contracts import (
    CONTRACT_SCHEMA_VERSION,
    ClinicalEvidenceBundle,
    ClinicalEvidenceItem,
    ClinicalSourceReference,
    EvidenceErrorCode,
    EvidenceOrigin,
    EvidenceStatus,
    FunctionalAssessmentResult,
    OntologyResolutionResult,
    RecertificationResult,
    RuntimeStageStatus,
    RuntimeTrace,
    TerminalStatusResult,
)
from app.domain.clinical_runtime.serialization import to_serializable


def _source_ref(**overrides) -> ClinicalSourceReference:
    defaults = dict(
        source_type="STRUCTURED_FIELD",
        source_id="rn-recert-assessment:123",
        source_record_type="RNRecertAssessment",
        source_field="pps_score",
    )
    defaults.update(overrides)
    return ClinicalSourceReference(**defaults)


def test_clinical_source_reference_preserves_provenance_fields():
    ref = _source_ref(source_author_id="nurse-42", source_version="v1")
    assert ref.source_type == "STRUCTURED_FIELD"
    assert ref.source_author_id == "nurse-42"
    assert ref.source_version == "v1"


def test_clinical_evidence_item_requires_status_and_source_reference():
    patient_id = uuid4()
    item = ClinicalEvidenceItem(
        evidence_id="ev-1",
        patient_id=patient_id,
        concept_code="PPS",
        canonical_name="Palliative Performance Scale",
        status=EvidenceStatus.DOCUMENTED,
        origin=EvidenceOrigin.AUTHORITATIVE_DATABASE,
        source_reference=_source_ref(),
        observed_value=40,
        normalized_value=40,
    )
    assert item.status == EvidenceStatus.DOCUMENTED
    assert item.source_reference.source_field == "pps_score"
    assert item.warnings == []


def test_documented_and_ai_estimated_are_distinct_statuses():
    documented = EvidenceStatus.DOCUMENTED
    estimated = EvidenceStatus.AI_ESTIMATED
    assert documented != estimated
    assert documented.value == "DOCUMENTED"
    assert estimated.value == "AI_ESTIMATED"


def test_clinical_evidence_items_are_immutable():
    item = ClinicalEvidenceItem(
        evidence_id="ev-2",
        patient_id=uuid4(),
        concept_code="KPS",
        canonical_name="Karnofsky Performance Scale",
        status=EvidenceStatus.DOCUMENTED,
        origin=EvidenceOrigin.AUTHORITATIVE_DATABASE,
        source_reference=_source_ref(source_field="kps_score"),
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        item.observed_value = 50  # type: ignore[misc]


def test_clinical_evidence_bundle_lookup_by_concept_code():
    patient_id = uuid4()
    pps_item = ClinicalEvidenceItem(
        evidence_id="ev-3",
        patient_id=patient_id,
        concept_code="PPS",
        canonical_name="Palliative Performance Scale",
        status=EvidenceStatus.DOCUMENTED,
        origin=EvidenceOrigin.AUTHORITATIVE_DATABASE,
        source_reference=_source_ref(source_field="pps_score"),
    )
    kps_item = ClinicalEvidenceItem(
        evidence_id="ev-4",
        patient_id=patient_id,
        concept_code="KPS",
        canonical_name="Karnofsky Performance Scale",
        status=EvidenceStatus.MISSING,
        source_reference=_source_ref(source_field="kps_score"),
    )
    bundle = ClinicalEvidenceBundle(
        patient_id=patient_id,
        items=[pps_item, kps_item],
        generated_at=datetime.now(timezone.utc),
    )
    assert bundle.by_concept_code("PPS") == [pps_item]
    assert bundle.by_concept_code("KPS") == [kps_item]
    assert bundle.by_concept_code("NYHA") == []


def test_evidence_error_codes_are_the_required_set():
    required = {
        "EVIDENCE_SOURCE_UNAVAILABLE",
        "EVIDENCE_SOURCE_UNAUTHORIZED",
        "EVIDENCE_NORMALIZATION_FAILED",
        "EVIDENCE_CONFLICT",
        "EVIDENCE_INCOMPLETE",
        "EVIDENCE_PROVENANCE_MISSING",
    }
    assert {e.value for e in EvidenceErrorCode} == required


def test_functional_assessment_result_tracks_missing_components():
    result = FunctionalAssessmentResult(
        instrument="FAST",
        value=None,
        normalized_value=None,
        status=EvidenceStatus.MISSING,
        complete=False,
        components_missing=["cognitive_decline_stage"],
    )
    assert result.complete is False
    assert "cognitive_decline_stage" in result.components_missing


def test_terminal_status_result_defaults_to_human_review_required():
    result = TerminalStatusResult(
        patient_id=uuid4(),
        disease_family="ALS",
        framework_version="v1",
        result_status=EvidenceStatus.UNVERIFIED,
    )
    assert result.human_review_required is True


def test_recertification_result_carries_current_evidence_bundle():
    patient_id = uuid4()
    bundle = ClinicalEvidenceBundle(patient_id=patient_id)
    result = RecertificationResult(
        benefit_period_id=uuid4(),
        framework_version="v1",
        current_evidence=bundle,
    )
    assert result.current_evidence is bundle
    assert result.human_review_required is True


def test_runtime_trace_requires_started_at_and_stage():
    trace = RuntimeTrace(
        trace_id="trace-1",
        patient_id=uuid4(),
        pipeline_version="v1",
        stage="EVIDENCE_HARVESTER",
        status=RuntimeStageStatus.STARTED,
        started_at=datetime.now(timezone.utc),
    )
    assert trace.stage == "EVIDENCE_HARVESTER"
    assert trace.actor_type == "SYSTEM"


def test_ontology_resolution_result_optional_by_default():
    result = OntologyResolutionResult()
    assert result.ontology_id is None
    assert result.ambiguity is False
    assert result.warnings == []


# =========================================================
# Commit 1 quality-gate tests (schema version, tz-aware
# timestamps, JSON serialization, redacted repr)
# =========================================================


def test_naive_datetime_rejected_on_source_reference():
    with pytest.raises(ValueError, match="timezone-aware"):
        ClinicalSourceReference(
            source_type="STRUCTURED_FIELD",
            source_recorded_at=datetime(2026, 1, 1),  # naive
        )


def test_naive_datetime_rejected_on_evidence_item():
    with pytest.raises(ValueError, match="timezone-aware"):
        ClinicalEvidenceItem(
            evidence_id="ev-naive",
            patient_id=uuid4(),
            concept_code="PPS",
            canonical_name="Palliative Performance Scale",
            status=EvidenceStatus.DOCUMENTED,
            origin=EvidenceOrigin.AUTHORITATIVE_DATABASE,
            source_reference=_source_ref(),
            recorded_at=datetime(2026, 1, 1),  # naive
        )


def test_naive_datetime_rejected_on_runtime_trace():
    with pytest.raises(ValueError, match="timezone-aware"):
        RuntimeTrace(
            trace_id="trace-naive",
            patient_id=uuid4(),
            pipeline_version="v1",
            stage="EVIDENCE_HARVESTER",
            status=RuntimeStageStatus.STARTED,
            started_at=datetime(2026, 1, 1),  # naive
        )


def test_timezone_aware_datetime_accepted():
    item = ClinicalEvidenceItem(
        evidence_id="ev-tz",
        patient_id=uuid4(),
        concept_code="PPS",
        canonical_name="Palliative Performance Scale",
        status=EvidenceStatus.DOCUMENTED,
        origin=EvidenceOrigin.AUTHORITATIVE_DATABASE,
        source_reference=_source_ref(),
        recorded_at=datetime.now(timezone.utc),
    )
    assert item.recorded_at.tzinfo is not None


def test_contracts_carry_schema_version():
    item = ClinicalEvidenceItem(
        evidence_id="ev-schema",
        patient_id=uuid4(),
        concept_code="PPS",
        canonical_name="Palliative Performance Scale",
        status=EvidenceStatus.DOCUMENTED,
        origin=EvidenceOrigin.AUTHORITATIVE_DATABASE,
        source_reference=_source_ref(),
    )
    assert item.schema_version == CONTRACT_SCHEMA_VERSION


def test_evidence_item_repr_does_not_leak_observed_value():
    item = ClinicalEvidenceItem(
        evidence_id="ev-repr",
        patient_id=uuid4(),
        concept_code="PPS",
        canonical_name="Palliative Performance Scale",
        status=EvidenceStatus.DOCUMENTED,
        origin=EvidenceOrigin.AUTHORITATIVE_DATABASE,
        source_reference=_source_ref(),
        observed_value="SENSITIVE_CLINICAL_VALUE_123",
    )
    rendered = repr(item)
    assert "SENSITIVE_CLINICAL_VALUE_123" not in rendered
    assert "ev-repr" in rendered
    assert "PPS" in rendered


def test_to_serializable_round_trips_enum_and_datetime():
    now = datetime.now(timezone.utc)
    item = ClinicalEvidenceItem(
        evidence_id="ev-json",
        patient_id=uuid4(),
        concept_code="PPS",
        canonical_name="Palliative Performance Scale",
        status=EvidenceStatus.DOCUMENTED,
        origin=EvidenceOrigin.AUTHORITATIVE_DATABASE,
        source_reference=_source_ref(),
        recorded_at=now,
    )
    payload = to_serializable(item)
    assert payload["status"] == "DOCUMENTED"
    assert payload["recorded_at"] == now.isoformat()
    assert payload["patient_id"] == str(item.patient_id)
    # must be actually JSON-serializable (no custom objects left over)
    import json

    json.dumps(payload)


def test_to_serializable_rejects_naive_datetime_directly():
    with pytest.raises(ValueError, match="naive datetime"):
        to_serializable(datetime(2026, 1, 1))


def test_empty_evidence_bundle_serializes_cleanly():
    bundle = ClinicalEvidenceBundle(patient_id=uuid4())
    payload = to_serializable(bundle)
    assert payload["items"] == []
    assert payload["errors"] == []


def test_functional_assessment_result_carries_calculation_and_ontology_version():
    result = FunctionalAssessmentResult(
        instrument="PPS",
        value=40,
        normalized_value=40,
        status=EvidenceStatus.CALCULATED,
        complete=True,
        calculation_version="pps-calc-v1",
        ontology_version="functional-assessment-framework-v1",
    )
    assert result.calculation_version == "pps-calc-v1"
    assert result.ontology_version == "functional-assessment-framework-v1"


def test_runtime_trace_status_values_are_stable_strings():
    assert {s.value for s in RuntimeStageStatus} == {
        "STARTED",
        "SUCCEEDED",
        "FAILED",
        "SKIPPED",
    }


def test_documented_status_requires_authoritative_database_origin():
    from app.domain.clinical_runtime.contracts import EvidenceOrigin

    with pytest.raises(ValueError, match="AUTHORITATIVE_DATABASE"):
        ClinicalEvidenceItem(
            evidence_id="ev-bad-origin",
            patient_id=uuid4(),
            concept_code="PPS",
            canonical_name="Palliative Performance Scale",
            status=EvidenceStatus.DOCUMENTED,
            source_reference=_source_ref(),
            origin=EvidenceOrigin.LEGACY_ADAPTER,
        )


def test_documented_status_allowed_with_authoritative_database_origin():
    from app.domain.clinical_runtime.contracts import EvidenceOrigin

    item = ClinicalEvidenceItem(
        evidence_id="ev-good-origin",
        patient_id=uuid4(),
        concept_code="PPS",
        canonical_name="Palliative Performance Scale",
        status=EvidenceStatus.DOCUMENTED,
        source_reference=_source_ref(),
        origin=EvidenceOrigin.AUTHORITATIVE_DATABASE,
    )
    assert item.origin == EvidenceOrigin.AUTHORITATIVE_DATABASE
