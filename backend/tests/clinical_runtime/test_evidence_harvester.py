"""
Commit 2 tests: ClinicalEvidenceHarvester (typed wrapper around
harvest_clinical_facts() producing a ClinicalEvidenceBundle).
"""

from uuid import uuid4

from app.domain.clinical_runtime.contracts import EvidenceStatus
from app.services.eligibility.evidence_harvester import (
    ClinicalEvidenceHarvester,
    PatientEvidenceContext,
    harvest_clinical_facts,
)


def _harvest(patient: dict, **kwargs):
    harvester = ClinicalEvidenceHarvester()
    context = PatientEvidenceContext(patient_id=uuid4(), patient=patient, **kwargs)
    return harvester.harvest(context)


def test_bundle_has_one_item_per_fact_key():
    bundle = _harvest({"pps": 40})
    expected_keys = set(harvest_clinical_facts({"pps": 40}).keys())
    actual_keys = {item.concept_code for item in bundle.items}
    assert actual_keys == expected_keys


def test_items_are_deterministically_ordered_by_concept_code():
    bundle = _harvest({"pps": 40, "kps": 50})
    codes = [item.concept_code for item in bundle.items]
    assert codes == sorted(codes)


def test_documented_value_classified_correctly():
    bundle = _harvest({"pps": 40})
    item = bundle.by_concept_code("pps")[0]
    assert item.status == EvidenceStatus.DOCUMENTED
    assert item.normalized_value == 40


def test_missing_value_classified_as_missing():
    bundle = _harvest({})
    item = bundle.by_concept_code("pps")[0]
    assert item.status == EvidenceStatus.MISSING
    assert item.normalized_value is None
    assert item.recorded_at is None


def test_out_of_range_ecog_classified_as_unverified_not_missing():
    # ECOG is 0-5; 9 is out of range and must not be silently discarded as
    # if no value had been supplied at all.
    bundle = _harvest({"ecog_score": 9})
    item = bundle.by_concept_code("ecog_score")[0]
    assert item.status == EvidenceStatus.UNVERIFIED
    assert item.normalized_value is None


def test_valid_ecog_in_range_is_documented():
    bundle = _harvest({"ecog_score": 3})
    item = bundle.by_concept_code("ecog_score")[0]
    assert item.status == EvidenceStatus.DOCUMENTED
    assert item.normalized_value == 3


def test_ecog_present_in_all_bundles_even_when_absent():
    bundle = _harvest({})
    assert bundle.by_concept_code("ecog_score")[0].status == EvidenceStatus.MISSING


def test_bundle_carries_encounter_and_benefit_period():
    benefit_period_id = uuid4()
    bundle = _harvest(
        {"pps": 40},
        encounter_id="enc-1",
        benefit_period_id=benefit_period_id,
    )
    assert bundle.encounter_id == "enc-1"
    assert bundle.benefit_period_id == benefit_period_id
    item = bundle.by_concept_code("pps")[0]
    assert item.encounter_id == "enc-1"
    assert item.benefit_period_id == benefit_period_id


def test_bundle_generated_at_is_timezone_aware():
    bundle = _harvest({"pps": 40})
    assert bundle.generated_at is not None
    assert bundle.generated_at.tzinfo is not None


def test_harvester_draws_no_eligibility_or_prognosis_conclusion():
    # The harvester must only classify/package facts -- it must never
    # produce an eligibility/certification/recertification/discharge verdict
    # anywhere in its output. There is no field for such a verdict in the
    # contract; this test guards against one being added by accident.
    bundle = _harvest({"pps": 40})
    payload_fields = {f for item in bundle.items for f in vars(item).keys()}
    forbidden_terms = {
        "eligible",
        "eligibility",
        "certification",
        "recertification",
        "prognosis",
        "terminal_status",
        "discharge",
    }
    for field_name in payload_fields:
        assert not any(term in field_name.lower() for term in forbidden_terms)


def test_evidence_item_source_field_matches_concept_code():
    bundle = _harvest({"pps": 40})
    item = bundle.by_concept_code("pps")[0]
    assert item.source_reference.source_field == "pps"
    assert item.source_reference.source_type == "STRUCTURED_FIELD"


def test_harvest_does_not_mutate_input_patient_dict():
    patient = {"pps": 40}
    _harvest(patient)
    assert patient == {"pps": 40}
