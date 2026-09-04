# tests/clinical_runtime/test_evidence_sources_2d_integration.py
"""
Commit 2D tests: structured conflict detection
(evidence_conflict_detection.detect_functional_score_conflicts), missing-
workflow-requirement detection (detect_missing_rn_recert_requirement), the
new EvidencePolarity.EXPLICIT_NEGATIVE contract validation, and the
harvester's canonical (non-UUID-lexical) chronology ordering -- against a
real, migrated isolated database via tests/conftest.py `db_session` -- no
mocking.

Covers the Commit 2D acceptance criteria:
  - DOCUMENTED_STATUS_PRESERVED_WHEN_CONFLICTING
  - STRUCTURED_CONFLICT_REFERENCES_BOTH_ITEMS
  - SAME_VALUE_IS_NOT_A_CONFLICT
  - SAME_PERIOD_DIFFERENT_VALUE_IS_VALUE_DISAGREEMENT
  - DIFFERENT_PERIOD_IS_TREND_NOT_CONFLICT
  - NO_AUTOMATIC_WINNER (resolution_status stays UNRESOLVED,
    winning_evidence_id stays None)
  - CONFLICT_COMPARISON_SCOPED_TO_BENEFIT_PERIOD
  - ECOG_CROSS_SOURCE_COMPARISON_NOT_ATTEMPTED (FIELD_NOT_AVAILABLE on the
    RN side -- see evidence_conflict_detection.FUNCTIONAL_SCORE_FIELD_MAP)
  - MISSING_RN_RECERT_REQUIREMENT_WHEN_BENEFIT_PERIOD_SCOPED_AND_ABSENT
  - MISSING_REQUIREMENT_NOT_PRODUCED_WITHOUT_EXPLICIT_BENEFIT_PERIOD_SCOPE
  - MISSING_REQUIREMENT_NOT_PRODUCED_WHEN_ASSESSMENT_EXISTS
  - EXPLICIT_NEGATIVE_POLARITY_REQUIRES_COMPLETE_SOURCE_IDENTITY
  - EXPLICIT_NEGATIVE_POLARITY_SUCCEEDS_WITH_COMPLETE_SOURCE
  - NULL_VALUE_IS_NOT_INFERRED_AS_EXPLICIT_NEGATIVE (default polarity is
    POSITIVE; nothing derives EXPLICIT_NEGATIVE from an absent value)
  - BUNDLE_CHRONOLOGICAL_ORDERS_BY_EFFECTIVE_AT_NOT_EVIDENCE_ID
  - HARVESTER_ORDERING_DOES_NOT_DEPEND_ON_UUID_LEXICAL_ORDER
  - NO_AUTONOMOUS_ELIGIBILITY/CERTIFICATION/RECERTIFICATION/PROGNOSIS/
    DISCHARGE conclusion anywhere in conflict/missing-requirement output

Explicitly out of scope / N/A (documented rather than fabricated):
  - "RNRecertAssessment ECOG vs F2FEncounter ECOG" conflict detection:
    RNRecertAssessment has no ecog_score_* field at all
    (app/models/rn_recert_assessment.py) -- FIELD_NOT_AVAILABLE, not tested
    as a conflict because there is nothing to compare.
  - Correction/addendum/entered-in-error relationship tests for
    RNRecertAssessment or F2FEncounter: neither model has any
    correction/supersession/addendum field. Certification's real
    supersession chain (superseded_by_id/superseded_at) is already covered
    by the existing Commit 2B tests
    (test_evidence_sources_2b_integration.py) surfacing
    correction_status="SUPERSEDED" -- not duplicated here.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from app.domain.clinical_runtime.contracts import (
    ClinicalEvidenceItem,
    ClinicalSourceReference,
    ConflictResolutionStatus,
    ConflictType,
    EvidenceOrigin,
    EvidencePolarity,
    EvidenceStatus,
)
from app.models.benefit_period import BenefitPeriod
from app.models.f2f_encounter import F2FEncounter
from app.models.patient import Patient
from app.models.rn_recert_assessment import RNRecertAssessment
from app.services.eligibility.clinical_evidence_harvester import ClinicalEvidenceHarvester
from app.services.eligibility.evidence_conflict_detection import (
    detect_functional_score_conflicts,
    detect_missing_rn_recert_requirement,
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
    return uuid.uuid5(uuid.NAMESPACE_URL, f"commit2d:{test_name}:{kind}")


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
# Structured conflict detection (real DB, real adapters)
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


def test_structured_conflict_references_both_source_items(db_session):
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


def test_different_effective_periods_preserved_as_trend_not_conflict(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "conflict_trend_not_conflict", tenant_id)
    bp_id = _seed_benefit_period(db_session, "conflict_trend_not_conflict", "a", patient_id=patient_id, tenant_id=tenant_id)
    _seed_assessment(
        db_session, "conflict_trend_not_conflict", "a", patient_id=patient_id, benefit_period_id=bp_id,
        tenant_id=tenant_id, pps_score=60, attested_at=datetime(2025, 1, 15, tzinfo=timezone.utc),
    )
    _seed_f2f(
        db_session, "conflict_trend_not_conflict", "a", patient_id=patient_id, benefit_period_id=bp_id,
        tenant_id=tenant_id, pps_score_current=40, encounter_date=date(2025, 2, 15),
    )

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=bp_id)
    assert bundle.conflicts == []
    # Both values remain present as ordinary evidence -- the decline is
    # visible via chronological ordering, not erased.
    values = {item.normalized_value.get("pps_score") or item.normalized_value.get("pps_score_current") for item in bundle.items}
    assert values == {60, 40}


def test_missing_effective_at_on_either_side_is_potential_conflict_not_auto_resolved(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "conflict_potential", tenant_id)
    bp_id = _seed_benefit_period(db_session, "conflict_potential", "a", patient_id=patient_id, tenant_id=tenant_id)
    _seed_assessment(
        db_session, "conflict_potential", "a", patient_id=patient_id, benefit_period_id=bp_id,
        tenant_id=tenant_id, pps_score=40, attested_at=None, finalized_at=None,
    )
    _seed_f2f(
        db_session, "conflict_potential", "a", patient_id=patient_id, benefit_period_id=bp_id,
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
    """ECOG only exists on F2FEncounter -- FIELD_NOT_AVAILABLE on RN side,
    so no ECOG conflict can ever be produced regardless of values."""
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
# Missing-workflow-requirement detection
# ---------------------------------------------------------------------


def test_missing_rn_recert_requirement_when_benefit_period_scoped_and_absent(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "missing_req_present", tenant_id)
    bp_id = _seed_benefit_period(db_session, "missing_req_present", "a", patient_id=patient_id, tenant_id=tenant_id)
    # No RNRecertAssessment seeded for this benefit period at all.

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=bp_id)
    assert len(bundle.missing_requirements) == 1
    requirement = bundle.missing_requirements[0]
    assert requirement.requirement_code == "RN_RECERT_ASSESSMENT_MISSING"
    assert requirement.expected_source_type == "RNRecertAssessment"
    assert requirement.benefit_period_id == bp_id
    assert requirement.human_review_required is True
    assert requirement.status == "MISSING"


def test_missing_requirement_not_produced_without_explicit_benefit_period_scope(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "missing_req_unscoped", tenant_id)
    _seed_benefit_period(db_session, "missing_req_unscoped", "a", patient_id=patient_id, tenant_id=tenant_id)

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id)
    assert bundle.missing_requirements == []


def test_missing_requirement_not_produced_when_assessment_exists(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "missing_req_satisfied", tenant_id)
    bp_id = _seed_benefit_period(db_session, "missing_req_satisfied", "a", patient_id=patient_id, tenant_id=tenant_id)
    _seed_assessment(db_session, "missing_req_satisfied", "a", patient_id=patient_id, benefit_period_id=bp_id, tenant_id=tenant_id)

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=bp_id)
    assert bundle.missing_requirements == []


# ---------------------------------------------------------------------
# EvidencePolarity.EXPLICIT_NEGATIVE contract validation (unit-level, no DB)
# ---------------------------------------------------------------------


def test_explicit_negative_polarity_requires_complete_source_identity():
    with pytest.raises(ValueError, match="EXPLICIT_NEGATIVE polarity requires"):
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


def test_default_polarity_is_positive_not_inferred_negative():
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
    # A null/absent observed_value never becomes EXPLICIT_NEGATIVE on its
    # own -- polarity defaults to POSITIVE and nothing in this contract
    # derives a negative finding from a merely missing value.
    assert item.polarity == EvidencePolarity.POSITIVE


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

    from app.domain.clinical_runtime.contracts import ClinicalEvidenceBundle

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
# No autonomous conclusion anywhere in conflict/missing-requirement output
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
# Unit-level tests for the conflict-detection functions directly (no DB) --
# exercises the pure comparison logic in isolation from adapter wiring.
# ---------------------------------------------------------------------


def _make_item(source_model, source_table, concept_code, normalized_value, *, patient_id, benefit_period_id, effective_at, evidence_id):
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
        origin=EvidenceOrigin.AUTHORITATIVE_DATABASE,
    )


def test_detect_functional_score_conflicts_pure_function_same_period():
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
    conflicts = detect_functional_score_conflicts(items)
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == ConflictType.VALUE_DISAGREEMENT


def test_detect_missing_rn_recert_requirement_pure_function():
    patient_id = uuid.uuid4()
    bp_id = uuid.uuid4()
    requirements = detect_missing_rn_recert_requirement([], patient_id=patient_id, benefit_period_id=bp_id)
    assert len(requirements) == 1
    assert requirements[0].requirement_code == "RN_RECERT_ASSESSMENT_MISSING"

    requirements_no_scope = detect_missing_rn_recert_requirement([], patient_id=patient_id, benefit_period_id=None)
    assert requirements_no_scope == []
