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


def _source_ref(*, patient_id, **overrides) -> ClinicalSourceReference:
    defaults = dict(
        source_type="STRUCTURED_FIELD",
        source_id="rn-recert-assessment:123",
        source_record_type="RN_RECERT_ASSESSMENT_RECORD",
        source_field="pps_score",
        source_model="RNRecertAssessment",
        source_table="rn_recert_assessments",
        source_patient_id=patient_id,
    )
    defaults.update(overrides)
    return ClinicalSourceReference(**defaults)


def test_clinical_source_reference_preserves_provenance_fields():
    ref = _source_ref(patient_id=uuid4(), source_author_id="nurse-42", source_version="v1")
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
        source_reference=_source_ref(patient_id=patient_id),
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
    patient_id = uuid4()
    item = ClinicalEvidenceItem(
        evidence_id="ev-2",
        patient_id=patient_id,
        concept_code="KPS",
        canonical_name="Karnofsky Performance Scale",
        status=EvidenceStatus.DOCUMENTED,
        origin=EvidenceOrigin.AUTHORITATIVE_DATABASE,
        source_reference=_source_ref(patient_id=patient_id, source_field="kps_score"),
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
        source_reference=_source_ref(patient_id=patient_id, source_field="pps_score"),
    )
    kps_item = ClinicalEvidenceItem(
        evidence_id="ev-4",
        patient_id=patient_id,
        concept_code="KPS",
        canonical_name="Karnofsky Performance Scale",
        status=EvidenceStatus.MISSING,
        source_reference=_source_ref(patient_id=patient_id, source_field="kps_score"),
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
    patient_id = uuid4()
    with pytest.raises(ValueError, match="timezone-aware"):
        ClinicalEvidenceItem(
            evidence_id="ev-naive",
            patient_id=patient_id,
            concept_code="PPS",
            canonical_name="Palliative Performance Scale",
            status=EvidenceStatus.DOCUMENTED,
            origin=EvidenceOrigin.AUTHORITATIVE_DATABASE,
            source_reference=_source_ref(patient_id=patient_id),
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
    patient_id = uuid4()
    item = ClinicalEvidenceItem(
        evidence_id="ev-tz",
        patient_id=patient_id,
        concept_code="PPS",
        canonical_name="Palliative Performance Scale",
        status=EvidenceStatus.DOCUMENTED,
        origin=EvidenceOrigin.AUTHORITATIVE_DATABASE,
        source_reference=_source_ref(patient_id=patient_id),
        recorded_at=datetime.now(timezone.utc),
    )
    assert item.recorded_at.tzinfo is not None


def test_contracts_carry_schema_version():
    patient_id = uuid4()
    item = ClinicalEvidenceItem(
        evidence_id="ev-schema",
        patient_id=patient_id,
        concept_code="PPS",
        canonical_name="Palliative Performance Scale",
        status=EvidenceStatus.DOCUMENTED,
        origin=EvidenceOrigin.AUTHORITATIVE_DATABASE,
        source_reference=_source_ref(patient_id=patient_id),
    )
    assert item.schema_version == CONTRACT_SCHEMA_VERSION


def test_evidence_item_repr_does_not_leak_observed_value():
    patient_id = uuid4()
    item = ClinicalEvidenceItem(
        evidence_id="ev-repr",
        patient_id=patient_id,
        concept_code="PPS",
        canonical_name="Palliative Performance Scale",
        status=EvidenceStatus.DOCUMENTED,
        origin=EvidenceOrigin.AUTHORITATIVE_DATABASE,
        source_reference=_source_ref(patient_id=patient_id),
        observed_value="SENSITIVE_CLINICAL_VALUE_123",
    )
    rendered = repr(item)
    assert "SENSITIVE_CLINICAL_VALUE_123" not in rendered
    assert "ev-repr" in rendered
    assert "PPS" in rendered


def test_to_serializable_round_trips_enum_and_datetime():
    now = datetime.now(timezone.utc)
    patient_id = uuid4()
    item = ClinicalEvidenceItem(
        evidence_id="ev-json",
        patient_id=patient_id,
        concept_code="PPS",
        canonical_name="Palliative Performance Scale",
        status=EvidenceStatus.DOCUMENTED,
        origin=EvidenceOrigin.AUTHORITATIVE_DATABASE,
        source_reference=_source_ref(patient_id=patient_id),
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
    patient_id = uuid4()
    with pytest.raises(ValueError, match="AUTHORITATIVE_DATABASE"):
        ClinicalEvidenceItem(
            evidence_id="ev-bad-origin",
            patient_id=patient_id,
            concept_code="PPS",
            canonical_name="Palliative Performance Scale",
            status=EvidenceStatus.DOCUMENTED,
            source_reference=_source_ref(patient_id=patient_id),
            origin=EvidenceOrigin.LEGACY_ADAPTER,
        )


def test_documented_status_allowed_with_authoritative_database_origin():
    patient_id = uuid4()
    item = ClinicalEvidenceItem(
        evidence_id="ev-good-origin",
        patient_id=patient_id,
        concept_code="PPS",
        canonical_name="Palliative Performance Scale",
        status=EvidenceStatus.DOCUMENTED,
        source_reference=_source_ref(patient_id=patient_id),
        origin=EvidenceOrigin.AUTHORITATIVE_DATABASE,
    )
    assert item.origin == EvidenceOrigin.AUTHORITATIVE_DATABASE


# =========================================================
# Commit 2A corrective verification: complete provenance
# identity is REQUIRED for DOCUMENTED evidence, not merely
# origin=AUTHORITATIVE_DATABASE. Each negative test below
# removes exactly one required identity field/consistency
# check and asserts construction fails.
# =========================================================


def _authoritative_kwargs(patient_id, **overrides):
    kwargs = dict(
        evidence_id="ev-provenance",
        patient_id=patient_id,
        concept_code="DIAGNOSIS",
        canonical_name="Malignant neoplasm of lung",
        status=EvidenceStatus.DOCUMENTED,
        origin=EvidenceOrigin.AUTHORITATIVE_DATABASE,
        source_reference=_source_ref(
            patient_id=patient_id,
            source_model="PatientDiagnosis",
            source_table="patient_diagnoses",
            source_field="icd10_code",
        ),
    )
    kwargs.update(overrides)
    return kwargs


def test_documented_requires_source_model():
    patient_id = uuid4()
    with pytest.raises(ValueError, match="source_model"):
        ClinicalEvidenceItem(
            **_authoritative_kwargs(
                patient_id,
                source_reference=_source_ref(patient_id=patient_id, source_model=None),
            )
        )


def test_documented_requires_source_table():
    patient_id = uuid4()
    with pytest.raises(ValueError, match="source_table"):
        ClinicalEvidenceItem(
            **_authoritative_kwargs(
                patient_id,
                source_reference=_source_ref(patient_id=patient_id, source_table=None),
            )
        )


def test_documented_requires_source_record_id():
    patient_id = uuid4()
    with pytest.raises(ValueError, match="source_id"):
        ClinicalEvidenceItem(
            **_authoritative_kwargs(
                patient_id,
                source_reference=_source_ref(patient_id=patient_id, source_id=None),
            )
        )


def test_documented_requires_source_field():
    patient_id = uuid4()
    with pytest.raises(ValueError, match="source_field"):
        ClinicalEvidenceItem(
            **_authoritative_kwargs(
                patient_id,
                source_reference=_source_ref(patient_id=patient_id, source_field=None),
            )
        )


def test_documented_requires_source_patient_id():
    patient_id = uuid4()
    with pytest.raises(ValueError, match="source_patient_id"):
        ClinicalEvidenceItem(
            **_authoritative_kwargs(
                patient_id,
                source_reference=_source_ref(patient_id=patient_id, source_patient_id=None),
            )
        )


def test_documented_rejects_source_patient_id_mismatch():
    patient_id = uuid4()
    other_patient_id = uuid4()
    with pytest.raises(ValueError, match="source_patient_id does not match"):
        ClinicalEvidenceItem(
            **_authoritative_kwargs(patient_id, source_reference=_source_ref(patient_id=other_patient_id))
        )


def test_documented_rejects_source_encounter_id_conflict():
    patient_id = uuid4()
    with pytest.raises(ValueError, match="source_encounter_id conflicts"):
        ClinicalEvidenceItem(
            **_authoritative_kwargs(
                patient_id,
                encounter_id="encounter-requested",
                source_reference=_source_ref(patient_id=patient_id, source_encounter_id="encounter-other"),
            )
        )


def test_documented_rejects_source_benefit_period_id_conflict():
    patient_id = uuid4()
    requested_bp = uuid4()
    other_bp = uuid4()
    with pytest.raises(ValueError, match="source_benefit_period_id conflicts"):
        ClinicalEvidenceItem(
            **_authoritative_kwargs(
                patient_id,
                benefit_period_id=requested_bp,
                source_reference=_source_ref(patient_id=patient_id, source_benefit_period_id=other_bp),
            )
        )


def test_legacy_adapter_item_must_not_be_documented():
    patient_id = uuid4()
    with pytest.raises(ValueError, match="AUTHORITATIVE_DATABASE"):
        ClinicalEvidenceItem(
            **_authoritative_kwargs(patient_id, origin=EvidenceOrigin.LEGACY_ADAPTER)
        )


def test_legacy_item_does_not_overwrite_authoritative_item_in_bundle():
    """
    A bundle may carry both an authoritative and a legacy item for the same
    concept -- the bundle itself does not silently merge/overwrite one with
    the other. Reconciliation precedence is Commit 2E scope; here we only
    verify both survive independently and remain distinguishable by origin.
    """
    patient_id = uuid4()
    authoritative_item = ClinicalEvidenceItem(**_authoritative_kwargs(patient_id, evidence_id="ev-authoritative"))
    legacy_item = ClinicalEvidenceItem(
        evidence_id="ev-legacy",
        patient_id=patient_id,
        concept_code="DIAGNOSIS",
        canonical_name="Malignant neoplasm of lung",
        status=EvidenceStatus.UNVERIFIED,
        origin=EvidenceOrigin.LEGACY_ADAPTER,
        source_reference=ClinicalSourceReference(source_type="LEGACY_STRUCTURED_FIELD"),
    )
    bundle = ClinicalEvidenceBundle(
        patient_id=patient_id,
        items=[authoritative_item, legacy_item],
        generated_at=datetime.now(timezone.utc),
    )
    concept_items = bundle.by_concept_code("DIAGNOSIS")
    assert authoritative_item in concept_items
    assert legacy_item in concept_items
    assert authoritative_item.origin == EvidenceOrigin.AUTHORITATIVE_DATABASE
    assert legacy_item.origin == EvidenceOrigin.LEGACY_ADAPTER


# --- Required positive tests -----------------------------------------


def test_complete_authoritative_documented_item_succeeds():
    patient_id = uuid4()
    item = ClinicalEvidenceItem(**_authoritative_kwargs(patient_id))
    assert item.status == EvidenceStatus.DOCUMENTED
    assert item.origin == EvidenceOrigin.AUTHORITATIVE_DATABASE
    assert item.source_reference.source_patient_id == patient_id


def test_legacy_adapter_item_succeeds_only_as_unverified_or_missing():
    patient_id = uuid4()
    for status in (EvidenceStatus.UNVERIFIED, EvidenceStatus.MISSING):
        item = ClinicalEvidenceItem(
            evidence_id=f"ev-legacy-{status.value}",
            patient_id=patient_id,
            concept_code="PPS",
            canonical_name="Palliative Performance Scale",
            status=status,
            origin=EvidenceOrigin.LEGACY_ADAPTER,
            source_reference=ClinicalSourceReference(source_type="LEGACY_STRUCTURED_FIELD"),
        )
        assert item.status in (EvidenceStatus.UNVERIFIED, EvidenceStatus.MISSING)
    with pytest.raises(ValueError):
        ClinicalEvidenceItem(
            evidence_id="ev-legacy-bad",
            patient_id=patient_id,
            concept_code="PPS",
            canonical_name="Palliative Performance Scale",
            status=EvidenceStatus.DOCUMENTED,
            origin=EvidenceOrigin.LEGACY_ADAPTER,
            source_reference=ClinicalSourceReference(source_type="LEGACY_STRUCTURED_FIELD"),
        )


def test_source_field_must_not_equal_source_table():
    with pytest.raises(ValueError, match="source_field must not contain a table name"):
        ClinicalSourceReference(
            source_type="DATABASE_RECORD",
            source_table="patient_diagnoses",
            source_field="patient_diagnoses",
        )
