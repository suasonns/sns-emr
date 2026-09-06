# tests/clinical_runtime/test_evidence_sources_2c_integration.py
"""
Commit 2C real-database integration tests: ClinicalEvidenceHarvester +
F2FEncounterSourceAdapter against a real, migrated isolated database (via
the standard tests/conftest.py `db_session` fixture) -- no mocking.

Covers the Commit 2C acceptance criteria:
  - PATIENT_ISOLATION
  - TENANT_ISOLATION
  - BENEFIT_PERIOD_ISOLATION
  - FUTURE_EFFECTIVE_EXCLUSION (as_of respected against encounter_date)
  - SOURCE_RECORD_RESOLUTION
  - PREVIOUS_VS_CURRENT_SCORE_PAIR_PRESERVED_AS_EVIDENCE (no
    decline/improvement conclusion computed by the adapter itself)
  - DETERMINISTIC (rerun produces identical evidence identities)
  - MISSING_PROVENANCE_HANDLING (unattested rows never fabricated)
  - NO_AUTONOMOUS_ELIGIBILITY/CERTIFICATION/PROGNOSIS conclusion
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from app.domain.clinical_runtime.contracts import EvidenceOrigin, EvidenceStatus
from app.models.benefit_period import BenefitPeriod
from app.models.f2f_encounter import F2FEncounter
from app.models.patient import Patient
from app.models.tenant import Tenant
from app.services.eligibility.clinical_evidence_harvester import ClinicalEvidenceHarvester

_TEST_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


def _seed_id(test_name: str, kind: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"commit2c:{test_name}:{kind}")


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
            ecog_score_previous=2,
            ecog_score_current=3,
        )
        defaults.update(fields)
        db_session.add(
            F2FEncounter(
                id=row_id,
                patient_id=patient_id,
                benefit_period_id=benefit_period_id,
                tenant_id=tenant_id,
                **defaults,
            )
        )
        db_session.commit()
    return row_id


def test_f2f_encounter_is_documented_with_authoritative_provenance(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "f2f_doc_provenance", tenant_id)
    bp_id = _seed_benefit_period(db_session, "f2f_doc_provenance", "a", patient_id=patient_id, tenant_id=tenant_id)
    row_id = _seed_f2f(
        db_session, "f2f_doc_provenance", "a", patient_id=patient_id, benefit_period_id=bp_id, tenant_id=tenant_id,
        attested_at=datetime(2025, 2, 2, tzinfo=timezone.utc), attesting_provider_user_id=_TEST_USER_ID,
    )

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id)
    items = bundle.by_concept_code("F2F_ENCOUNTER")
    assert len(items) == 1
    item = items[0]
    assert item.status == EvidenceStatus.DOCUMENTED
    assert item.origin == EvidenceOrigin.AUTHORITATIVE_DATABASE
    assert item.source_reference.source_model == "F2FEncounter"
    assert item.source_reference.source_table == "f2f_encounters"
    assert item.source_reference.source_id == str(row_id)
    assert item.source_reference.source_patient_id == patient_id
    assert item.source_reference.source_benefit_period_id == bp_id
    assert item.source_reference.authentication_status == "ATTESTED"
    assert item.normalized_value["ecog_score_previous"] == 2
    assert item.normalized_value["ecog_score_current"] == 3


def test_f2f_encounter_unattested_provenance_is_not_fabricated(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "f2f_unattested", tenant_id)
    bp_id = _seed_benefit_period(db_session, "f2f_unattested", "a", patient_id=patient_id, tenant_id=tenant_id)
    _seed_f2f(
        db_session, "f2f_unattested", "a", patient_id=patient_id, benefit_period_id=bp_id, tenant_id=tenant_id,
        status="DRAFT", attested_at=None, attesting_provider_user_id=None,
    )

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id)
    item = bundle.by_concept_code("F2F_ENCOUNTER")[0]
    assert item.source_reference.authentication_status == "UNATTESTED"
    assert item.source_reference.source_encounter_id is None


def test_f2f_cross_patient_evidence_is_not_leaked(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_a = _seed_patient(db_session, "f2f_isolation_a", tenant_id)
    patient_b = _seed_patient(db_session, "f2f_isolation_b", tenant_id)
    bp_a = _seed_benefit_period(db_session, "f2f_isolation_a", "a", patient_id=patient_a, tenant_id=tenant_id)
    bp_b = _seed_benefit_period(db_session, "f2f_isolation_b", "a", patient_id=patient_b, tenant_id=tenant_id)
    _seed_f2f(db_session, "f2f_isolation_a", "a", patient_id=patient_a, benefit_period_id=bp_a, tenant_id=tenant_id, ecog_score_current=1)
    _seed_f2f(db_session, "f2f_isolation_b", "a", patient_id=patient_b, benefit_period_id=bp_b, tenant_id=tenant_id, ecog_score_current=4)

    bundle_a = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_a, tenant_id=tenant_id)
    scores_a = {item.normalized_value["ecog_score_current"] for item in bundle_a.by_concept_code("F2F_ENCOUNTER")}
    assert scores_a == {1}


def test_f2f_cross_tenant_row_is_excluded(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    other_tenant_id = uuid.uuid4()
    if db_session.get(Tenant, other_tenant_id) is None:
        db_session.add(Tenant(id=other_tenant_id, legal_name="Other Hospice 2C", display_name="Other 2C", npi="7777777770"))
        db_session.commit()

    patient_id = _seed_patient(db_session, "f2f_tenant_isolation", tenant_id)
    bp_id = _seed_benefit_period(db_session, "f2f_tenant_isolation", "a", patient_id=patient_id, tenant_id=tenant_id)
    _seed_f2f(db_session, "f2f_tenant_isolation", "foreign", patient_id=patient_id, benefit_period_id=bp_id, tenant_id=other_tenant_id)
    _seed_f2f(db_session, "f2f_tenant_isolation", "own", patient_id=patient_id, benefit_period_id=bp_id, tenant_id=tenant_id)

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id)
    items = bundle.by_concept_code("F2F_ENCOUNTER")
    assert len(items) == 1
    assert items[0].source_reference.source_id == str(_seed_id("f2f_tenant_isolation", "f2f_own"))

    db_session.query(F2FEncounter).filter(
        F2FEncounter.id == _seed_id("f2f_tenant_isolation", "f2f_foreign")
    ).delete()
    db_session.query(Tenant).filter(Tenant.id == other_tenant_id).delete()
    db_session.commit()


def test_f2f_benefit_period_isolation(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "f2f_bp_isolation", tenant_id)
    bp_1 = _seed_benefit_period(db_session, "f2f_bp_isolation", "1", patient_id=patient_id, tenant_id=tenant_id, period_number=1)
    bp_2 = _seed_benefit_period(
        db_session, "f2f_bp_isolation", "2", patient_id=patient_id, tenant_id=tenant_id,
        benefit_type="RECERT", period_number=2, election_date=date(2025, 3, 1),
        start_date=date(2025, 3, 1), end_date=date(2025, 5, 1),
    )
    _seed_f2f(db_session, "f2f_bp_isolation", "1", patient_id=patient_id, benefit_period_id=bp_1, tenant_id=tenant_id, ecog_score_current=1)
    _seed_f2f(
        db_session, "f2f_bp_isolation", "2", patient_id=patient_id, benefit_period_id=bp_2, tenant_id=tenant_id,
        ecog_score_current=4, encounter_date=date(2025, 4, 1),
    )

    bundle = ClinicalEvidenceHarvester().harvest(
        db_session, patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=bp_2,
    )
    items = bundle.by_concept_code("F2F_ENCOUNTER")
    assert len(items) == 1
    assert items[0].normalized_value["ecog_score_current"] == 4


def test_f2f_future_effective_excluded_by_as_of(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "f2f_future_exclude", tenant_id)
    bp_id = _seed_benefit_period(db_session, "f2f_future_exclude", "a", patient_id=patient_id, tenant_id=tenant_id)
    _seed_f2f(
        db_session, "f2f_future_exclude", "a", patient_id=patient_id, benefit_period_id=bp_id, tenant_id=tenant_id,
        encounter_date=date(2025, 6, 1),
    )

    as_of = datetime(2025, 3, 1, tzinfo=timezone.utc)
    bundle = ClinicalEvidenceHarvester().harvest(
        db_session, patient_id=patient_id, tenant_id=tenant_id, as_of=as_of,
    )
    assert bundle.by_concept_code("F2F_ENCOUNTER") == []

    bundle_no_as_of = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id)
    assert len(bundle_no_as_of.by_concept_code("F2F_ENCOUNTER")) == 1


def test_f2f_rerun_produces_identical_evidence_identities(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "f2f_deterministic", tenant_id)
    bp_id = _seed_benefit_period(db_session, "f2f_deterministic", "a", patient_id=patient_id, tenant_id=tenant_id)
    _seed_f2f(db_session, "f2f_deterministic", "a", patient_id=patient_id, benefit_period_id=bp_id, tenant_id=tenant_id)

    bundle_1 = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id)
    bundle_2 = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id)

    ids_1 = [item.evidence_id for item in bundle_1.items]
    ids_2 = [item.evidence_id for item in bundle_2.items]
    assert ids_1 == ids_2


def test_f2f_harvester_draws_no_clinical_conclusion(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "f2f_no_conclusion", tenant_id)
    bp_id = _seed_benefit_period(db_session, "f2f_no_conclusion", "a", patient_id=patient_id, tenant_id=tenant_id)
    _seed_f2f(db_session, "f2f_no_conclusion", "a", patient_id=patient_id, benefit_period_id=bp_id, tenant_id=tenant_id)

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id)
    forbidden_terms = {"eligible", "eligibility", "certification", "recertification", "prognosis", "discharge"}
    for item in bundle.items:
        payload_fields = set(vars(item).keys())
        for field_name in payload_fields:
            assert not any(term in field_name.lower() for term in forbidden_terms)
        if item.normalized_value:
            for key in item.normalized_value:
                assert not any(term in key.lower() for term in forbidden_terms)
