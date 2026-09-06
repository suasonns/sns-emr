# tests/clinical_runtime/test_evidence_sources_2b_integration.py
"""
Commit 2B real-database integration tests: ClinicalEvidenceHarvester +
RNRecertAssessmentSourceAdapter + CertificationSourceAdapter against a real,
migrated isolated database (via the standard tests/conftest.py `db_session`
fixture) -- no mocking.

Covers the Commit 2B acceptance criteria:
  - PATIENT_ISOLATION
  - TENANT_ISOLATION (RNRecertAssessment.tenant_id is nullable -- verified
    that a row explicitly stamped with a different tenant is still excluded)
  - BENEFIT_PERIOD_ISOLATION
  - PRIOR_VS_CURRENT_SEPARATION (both assessments/certs returned, not
    collapsed to "the current one")
  - FUTURE_EFFECTIVE_EXCLUSION (as_of respected)
  - SOURCE_RECORD_RESOLUTION (source_reference identity matches the seeded
    row exactly)
  - DETERMINISTIC (rerun produces identical evidence identities)
  - MISSING_PROVENANCE_HANDLING (unattested/unattributed rows leave
    source_author_id/authentication_status honest, never fabricated)
  - NO_AUTONOMOUS_ELIGIBILITY/CERTIFICATION/PROGNOSIS conclusion
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from app.domain.clinical_runtime.contracts import EvidenceOrigin, EvidenceStatus
from app.models.benefit_period import BenefitPeriod
from app.models.certification import Certification
from app.models.patient import Patient
from app.models.rn_recert_assessment import RNRecertAssessment
from app.models.tenant import Tenant
from app.models.user import User
from app.services.eligibility.clinical_evidence_harvester import ClinicalEvidenceHarvester

_TEST_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


def _seed_id(test_name: str, kind: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"commit2b:{test_name}:{kind}")


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
            eligibility_recommendation="RECOMMEND_CONTINUE",
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


def _seed_certification(db_session, test_name, suffix, *, patient_id, benefit_period_id, tenant_id, **fields):
    row_id = _seed_id(test_name, f"cert_{suffix}")
    if db_session.get(Certification, row_id) is None:
        defaults = dict(
            cert_type="INITIAL",
            signed_at=datetime(2025, 1, 2, 12, 0, 0),
            effective_date=date(2025, 1, 1),
            signed_by_role="ATTENDING_PHYSICIAN",
            signed_by_user_id=_TEST_USER_ID,
            status="FINALIZED",
            physician_narrative="Continued decline consistent with terminal prognosis.",
        )
        defaults.update(fields)
        db_session.add(
            Certification(
                id=row_id,
                tenant_id=tenant_id,
                patient_id=patient_id,
                benefit_period_id=benefit_period_id,
                **defaults,
            )
        )
        db_session.commit()
    return row_id


# ---------------------------------------------------------------------
# RNRecertAssessmentSourceAdapter
# ---------------------------------------------------------------------


def test_rn_recert_assessment_is_documented_with_authoritative_provenance(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "rn_doc_provenance", tenant_id)
    bp_id = _seed_benefit_period(db_session, "rn_doc_provenance", "a", patient_id=patient_id, tenant_id=tenant_id)
    row_id = _seed_assessment(
        db_session, "rn_doc_provenance", "a", patient_id=patient_id, benefit_period_id=bp_id, tenant_id=tenant_id,
        attested_at=datetime(2025, 1, 5, tzinfo=timezone.utc), attesting_provider_user_id=_TEST_USER_ID,
    )

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id)
    items = bundle.by_concept_code("RN_RECERT_ASSESSMENT")
    assert len(items) == 1
    item = items[0]
    assert item.status == EvidenceStatus.DOCUMENTED
    assert item.origin == EvidenceOrigin.AUTHORITATIVE_DATABASE
    assert item.source_reference.source_model == "RNRecertAssessment"
    assert item.source_reference.source_table == "rn_recert_assessments"
    assert item.source_reference.source_id == str(row_id)
    assert item.source_reference.source_patient_id == patient_id
    assert item.source_reference.source_benefit_period_id == bp_id
    assert item.source_reference.authentication_status == "ATTESTED"
    assert item.normalized_value["pps_score"] == 40
    # eligibility_recommendation must never be surfaced as evidence.
    assert "eligibility_recommendation" not in item.normalized_value


def test_rn_recert_assessment_unattested_provenance_is_not_fabricated(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "rn_unattested", tenant_id)
    bp_id = _seed_benefit_period(db_session, "rn_unattested", "a", patient_id=patient_id, tenant_id=tenant_id)
    _seed_assessment(
        db_session, "rn_unattested", "a", patient_id=patient_id, benefit_period_id=bp_id, tenant_id=tenant_id,
        status="DRAFT", attested_at=None, attesting_provider_user_id=None,
    )

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id)
    item = bundle.by_concept_code("RN_RECERT_ASSESSMENT")[0]
    assert item.source_reference.authentication_status == "UNATTESTED"
    assert item.source_reference.source_encounter_id is None


def test_rn_recert_cross_patient_evidence_is_not_leaked(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_a = _seed_patient(db_session, "rn_isolation_a", tenant_id)
    patient_b = _seed_patient(db_session, "rn_isolation_b", tenant_id)
    bp_a = _seed_benefit_period(db_session, "rn_isolation_a", "a", patient_id=patient_a, tenant_id=tenant_id)
    bp_b = _seed_benefit_period(db_session, "rn_isolation_b", "a", patient_id=patient_b, tenant_id=tenant_id)
    _seed_assessment(db_session, "rn_isolation_a", "a", patient_id=patient_a, benefit_period_id=bp_a, tenant_id=tenant_id, pps_score=40)
    _seed_assessment(db_session, "rn_isolation_b", "a", patient_id=patient_b, benefit_period_id=bp_b, tenant_id=tenant_id, pps_score=70)

    bundle_a = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_a, tenant_id=tenant_id)
    scores_a = {item.normalized_value["pps_score"] for item in bundle_a.by_concept_code("RN_RECERT_ASSESSMENT")}
    assert scores_a == {40}


def test_rn_recert_cross_tenant_row_is_excluded(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    other_tenant_id = uuid.uuid4()
    if db_session.get(Tenant, other_tenant_id) is None:
        db_session.add(Tenant(id=other_tenant_id, legal_name="Other Hospice 2B", display_name="Other 2B", npi="8888888880"))
        db_session.commit()

    patient_id = _seed_patient(db_session, "rn_tenant_isolation", tenant_id)
    bp_id = _seed_benefit_period(db_session, "rn_tenant_isolation", "a", patient_id=patient_id, tenant_id=tenant_id)
    # Same patient row, but this specific assessment is stamped with a
    # DIFFERENT tenant_id (simulating a misattributed/foreign row) -- must
    # be excluded even though tenant_id is nullable on this model.
    _seed_assessment(
        db_session, "rn_tenant_isolation", "foreign", patient_id=patient_id, benefit_period_id=bp_id,
        tenant_id=other_tenant_id,
    )
    _seed_assessment(
        db_session, "rn_tenant_isolation", "own", patient_id=patient_id, benefit_period_id=bp_id,
        tenant_id=tenant_id,
    )

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id)
    items = bundle.by_concept_code("RN_RECERT_ASSESSMENT")
    assert len(items) == 1
    assert items[0].source_reference.source_id == str(_seed_id("rn_tenant_isolation", "assess_own"))

    db_session.query(RNRecertAssessment).filter(
        RNRecertAssessment.id == _seed_id("rn_tenant_isolation", "assess_foreign")
    ).delete()
    db_session.query(Tenant).filter(Tenant.id == other_tenant_id).delete()
    db_session.commit()


def test_rn_recert_benefit_period_isolation(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "rn_bp_isolation", tenant_id)
    bp_1 = _seed_benefit_period(db_session, "rn_bp_isolation", "1", patient_id=patient_id, tenant_id=tenant_id, period_number=1)
    bp_2 = _seed_benefit_period(
        db_session, "rn_bp_isolation", "2", patient_id=patient_id, tenant_id=tenant_id,
        benefit_type="RECERT", period_number=2, election_date=date(2025, 3, 1),
        start_date=date(2025, 3, 1), end_date=date(2025, 5, 1),
    )
    _seed_assessment(db_session, "rn_bp_isolation", "1", patient_id=patient_id, benefit_period_id=bp_1, tenant_id=tenant_id, pps_score=50)
    _seed_assessment(db_session, "rn_bp_isolation", "2", patient_id=patient_id, benefit_period_id=bp_2, tenant_id=tenant_id, pps_score=30)

    bundle = ClinicalEvidenceHarvester().harvest(
        db_session, patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=bp_1,
    )
    items = bundle.by_concept_code("RN_RECERT_ASSESSMENT")
    assert len(items) == 1
    assert items[0].normalized_value["pps_score"] == 50


def test_rn_recert_prior_and_current_assessments_both_preserved(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "rn_prior_current", tenant_id)
    bp_id = _seed_benefit_period(db_session, "rn_prior_current", "a", patient_id=patient_id, tenant_id=tenant_id)
    _seed_assessment(
        db_session, "rn_prior_current", "prior", patient_id=patient_id, benefit_period_id=bp_id, tenant_id=tenant_id,
        pps_score=60,
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
    _seed_assessment(
        db_session, "rn_prior_current", "current", patient_id=patient_id, benefit_period_id=bp_id, tenant_id=tenant_id,
        pps_score=40,
        created_at=datetime(2025, 2, 1, tzinfo=timezone.utc),
    )

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id)
    scores = {item.normalized_value["pps_score"] for item in bundle.by_concept_code("RN_RECERT_ASSESSMENT")}
    # Both preserved -- never collapsed to "just the current one". (Final
    # cross-adapter ordering is by (concept_code, evidence_id), not
    # created_at, so this asserts presence/preservation rather than order.)
    assert scores == {60, 40}


def test_rn_recert_future_effective_assessment_excluded_by_as_of(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "rn_future_exclude", tenant_id)
    bp_id = _seed_benefit_period(db_session, "rn_future_exclude", "a", patient_id=patient_id, tenant_id=tenant_id)
    _seed_assessment(
        db_session, "rn_future_exclude", "a", patient_id=patient_id, benefit_period_id=bp_id, tenant_id=tenant_id,
        attested_at=datetime(2025, 6, 1, tzinfo=timezone.utc), attesting_provider_user_id=_TEST_USER_ID,
    )

    as_of = datetime(2025, 3, 1, tzinfo=timezone.utc)
    bundle = ClinicalEvidenceHarvester().harvest(
        db_session, patient_id=patient_id, tenant_id=tenant_id, as_of=as_of,
    )
    assert bundle.by_concept_code("RN_RECERT_ASSESSMENT") == []

    bundle_no_as_of = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id)
    assert len(bundle_no_as_of.by_concept_code("RN_RECERT_ASSESSMENT")) == 1


# ---------------------------------------------------------------------
# CertificationSourceAdapter
# ---------------------------------------------------------------------


def test_certification_is_documented_with_authoritative_provenance(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "cert_doc_provenance", tenant_id)
    bp_id = _seed_benefit_period(db_session, "cert_doc_provenance", "a", patient_id=patient_id, tenant_id=tenant_id)
    row_id = _seed_certification(db_session, "cert_doc_provenance", "a", patient_id=patient_id, benefit_period_id=bp_id, tenant_id=tenant_id)

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id)
    items = bundle.by_concept_code("CERTIFICATION")
    assert len(items) == 1
    item = items[0]
    assert item.status == EvidenceStatus.DOCUMENTED
    assert item.origin == EvidenceOrigin.AUTHORITATIVE_DATABASE
    assert item.source_reference.source_model == "Certification"
    assert item.source_reference.source_table == "certifications"
    assert item.source_reference.source_id == str(row_id)
    assert item.source_reference.source_patient_id == patient_id
    assert item.source_reference.source_benefit_period_id == bp_id
    assert item.normalized_value["cert_type"] == "INITIAL"


def test_certification_cross_patient_evidence_is_not_leaked(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_a = _seed_patient(db_session, "cert_isolation_a", tenant_id)
    patient_b = _seed_patient(db_session, "cert_isolation_b", tenant_id)
    bp_a = _seed_benefit_period(db_session, "cert_isolation_a", "a", patient_id=patient_a, tenant_id=tenant_id)
    bp_b = _seed_benefit_period(db_session, "cert_isolation_b", "a", patient_id=patient_b, tenant_id=tenant_id)
    _seed_certification(db_session, "cert_isolation_a", "a", patient_id=patient_a, benefit_period_id=bp_a, tenant_id=tenant_id, cert_type="INITIAL")
    _seed_certification(db_session, "cert_isolation_b", "a", patient_id=patient_b, benefit_period_id=bp_b, tenant_id=tenant_id, cert_type="RECERT")

    bundle_a = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_a, tenant_id=tenant_id)
    types_a = {item.normalized_value["cert_type"] for item in bundle_a.by_concept_code("CERTIFICATION")}
    assert types_a == {"INITIAL"}


def test_certification_benefit_period_isolation(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "cert_bp_isolation", tenant_id)
    bp_1 = _seed_benefit_period(db_session, "cert_bp_isolation", "1", patient_id=patient_id, tenant_id=tenant_id, period_number=1)
    bp_2 = _seed_benefit_period(
        db_session, "cert_bp_isolation", "2", patient_id=patient_id, tenant_id=tenant_id,
        benefit_type="RECERT", period_number=2, election_date=date(2025, 3, 1),
        start_date=date(2025, 3, 1), end_date=date(2025, 5, 1),
    )
    _seed_certification(db_session, "cert_bp_isolation", "1", patient_id=patient_id, benefit_period_id=bp_1, tenant_id=tenant_id, cert_type="INITIAL")
    _seed_certification(
        db_session, "cert_bp_isolation", "2", patient_id=patient_id, benefit_period_id=bp_2, tenant_id=tenant_id,
        cert_type="RECERT", signed_at=datetime(2025, 3, 2, 12, 0, 0), effective_date=date(2025, 3, 1),
    )

    bundle = ClinicalEvidenceHarvester().harvest(
        db_session, patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=bp_2,
    )
    items = bundle.by_concept_code("CERTIFICATION")
    assert len(items) == 1
    assert items[0].normalized_value["cert_type"] == "RECERT"


def test_certification_future_effective_excluded_by_as_of(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "cert_future_exclude", tenant_id)
    bp_id = _seed_benefit_period(db_session, "cert_future_exclude", "a", patient_id=patient_id, tenant_id=tenant_id)
    _seed_certification(
        db_session, "cert_future_exclude", "a", patient_id=patient_id, benefit_period_id=bp_id, tenant_id=tenant_id,
        effective_date=date(2025, 6, 1), signed_at=datetime(2025, 6, 1, 12, 0, 0),
    )

    as_of = datetime(2025, 3, 1, tzinfo=timezone.utc)
    bundle = ClinicalEvidenceHarvester().harvest(
        db_session, patient_id=patient_id, tenant_id=tenant_id, as_of=as_of,
    )
    assert bundle.by_concept_code("CERTIFICATION") == []


def test_certification_supersession_is_preserved_as_evidence_not_conclusion(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "cert_supersession", tenant_id)
    bp_1 = _seed_benefit_period(db_session, "cert_supersession", "1", patient_id=patient_id, tenant_id=tenant_id, period_number=1)
    bp_2 = _seed_benefit_period(
        db_session, "cert_supersession", "2", patient_id=patient_id, tenant_id=tenant_id,
        benefit_type="RECERT", period_number=2, election_date=date(2025, 3, 1),
        start_date=date(2025, 3, 1), end_date=date(2025, 5, 1),
    )
    prior_id = _seed_certification(db_session, "cert_supersession", "prior", patient_id=patient_id, benefit_period_id=bp_1, tenant_id=tenant_id)
    current_id = _seed_certification(
        db_session, "cert_supersession", "current", patient_id=patient_id, benefit_period_id=bp_2, tenant_id=tenant_id,
        cert_type="RECERT", signed_at=datetime(2025, 3, 2, 12, 0, 0), effective_date=date(2025, 3, 1),
    )
    prior_row = db_session.get(Certification, prior_id)
    prior_row.status = "SUPERSEDED"
    prior_row.superseded_by_id = current_id
    prior_row.superseded_at = datetime(2025, 3, 2, 12, 0, 0, tzinfo=timezone.utc)
    db_session.commit()

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id)
    items = {item.source_reference.source_id: item for item in bundle.by_concept_code("CERTIFICATION")}
    assert len(items) == 2
    prior_item = items[str(prior_id)]
    assert prior_item.source_reference.correction_status == "SUPERSEDED"
    assert prior_item.normalized_value["superseded_by_id"] == str(current_id)


# ---------------------------------------------------------------------
# Cross-adapter: determinism and no-conclusion guard
# ---------------------------------------------------------------------


def test_2b_rerun_produces_identical_evidence_identities(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "2b_deterministic", tenant_id)
    bp_id = _seed_benefit_period(db_session, "2b_deterministic", "a", patient_id=patient_id, tenant_id=tenant_id)
    _seed_assessment(db_session, "2b_deterministic", "a", patient_id=patient_id, benefit_period_id=bp_id, tenant_id=tenant_id)
    _seed_certification(db_session, "2b_deterministic", "a", patient_id=patient_id, benefit_period_id=bp_id, tenant_id=tenant_id)

    bundle_1 = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id)
    bundle_2 = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id)

    ids_1 = [item.evidence_id for item in bundle_1.items]
    ids_2 = [item.evidence_id for item in bundle_2.items]
    assert ids_1 == ids_2


def test_2b_harvester_draws_no_clinical_conclusion(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "2b_no_conclusion", tenant_id)
    bp_id = _seed_benefit_period(db_session, "2b_no_conclusion", "a", patient_id=patient_id, tenant_id=tenant_id)
    _seed_assessment(db_session, "2b_no_conclusion", "a", patient_id=patient_id, benefit_period_id=bp_id, tenant_id=tenant_id)
    _seed_certification(db_session, "2b_no_conclusion", "a", patient_id=patient_id, benefit_period_id=bp_id, tenant_id=tenant_id)

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id)
    forbidden_terms = {"eligible", "eligibility", "recertification", "prognosis", "discharge"}
    for item in bundle.items:
        payload_fields = set(vars(item).keys())
        for field_name in payload_fields:
            assert not any(term in field_name.lower() for term in forbidden_terms)
        if item.normalized_value:
            for key in item.normalized_value:
                assert not any(term in key.lower() for term in forbidden_terms)
