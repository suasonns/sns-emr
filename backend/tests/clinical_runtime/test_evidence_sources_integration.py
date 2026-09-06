# tests/clinical_runtime/test_evidence_sources_integration.py
"""
Commit 2A real-database integration tests: ClinicalEvidenceHarvester +
DiagnosisSourceAdapter against a real, migrated isolated database (via the
standard tests/conftest.py `db_session` fixture) -- no mocking.

Covers the Commit 2A acceptance criteria:
  - DATABASE_BACKED_SOURCE_ACQUISITION
  - AUTHORITATIVE_PROVENANCE
  - PATIENT_ISOLATION
  - DIAGNOSIS_LIFECYCLE (active vs resolved vs historical)
  - DETERMINISTIC (rerun produces identical evidence identities)
  - NO_AUTONOMOUS_ELIGIBILITY/CERTIFICATION/PROGNOSIS
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.domain.clinical_runtime.contracts import EvidenceOrigin, EvidenceStatus
from app.models.patient import Patient
from app.models.patient_diagnosis import PatientDiagnosis
from app.models.tenant import Tenant
from app.services.eligibility.clinical_evidence_harvester import (
    ClinicalEvidenceHarvester,
    CrossTenantAccessError,
    PatientNotFoundError,
)


def _seed_id(test_name: str, kind: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"commit2a:{test_name}:{kind}")


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


def _seed_diagnosis(db_session, test_name, suffix, *, patient_id, tenant_id, **fields):
    dx_id = _seed_id(test_name, f"dx_{suffix}")
    if db_session.get(PatientDiagnosis, dx_id) is None:
        defaults = dict(
            diagnosis_type="PRIMARY",
            status="ACTIVE",
            source="ATTENDING_PHYSICIAN",
            icd10_code="C34.90",
            diagnosis_description="Malignant neoplasm of lung",
            display_name="Malignant neoplasm of lung",
            is_terminal=True,
            active=True,
            effective_date=date(2025, 1, 1),
        )
        defaults.update(fields)
        db_session.add(
            PatientDiagnosis(id=dx_id, tenant_id=tenant_id, patient_id=patient_id, **defaults)
        )
        db_session.commit()
    return dx_id


def test_diagnosis_evidence_is_documented_with_authoritative_provenance(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "doc_provenance", tenant_id)
    dx_id = _seed_diagnosis(db_session, "doc_provenance", "primary", patient_id=patient_id, tenant_id=tenant_id)

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id)

    dx_items = bundle.by_concept_code("DIAGNOSIS")
    assert len(dx_items) == 1
    item = dx_items[0]
    assert item.status == EvidenceStatus.DOCUMENTED
    assert item.origin == EvidenceOrigin.AUTHORITATIVE_DATABASE
    assert item.source_reference.source_model == "PatientDiagnosis"
    assert item.source_reference.source_table == "patient_diagnoses"
    assert item.source_reference.source_id == str(dx_id)
    assert item.normalized_value["clinical_status"] == "ACTIVE"


def test_resolved_diagnosis_is_not_active(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "resolved_dx", tenant_id)
    _seed_diagnosis(
        db_session, "resolved_dx", "resolved", patient_id=patient_id, tenant_id=tenant_id,
        status="ACTIVE", active=False, resolved_date=date(2025, 6, 1),
    )

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id)
    item = bundle.by_concept_code("DIAGNOSIS")[0]
    assert item.normalized_value["clinical_status"] == "RESOLVED"
    assert item.normalized_value["clinical_status"] != "ACTIVE"


def test_historical_diagnosis_status_is_preserved_not_active(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "historical_dx", tenant_id)
    _seed_diagnosis(
        db_session, "historical_dx", "hist", patient_id=patient_id, tenant_id=tenant_id,
        status="HISTORICAL",
    )

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id)
    item = bundle.by_concept_code("DIAGNOSIS")[0]
    assert item.normalized_value["clinical_status"] == "HISTORICAL"


def test_cross_patient_evidence_is_not_leaked(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_a = _seed_patient(db_session, "isolation_a", tenant_id)
    patient_b = _seed_patient(db_session, "isolation_b", tenant_id)
    _seed_diagnosis(db_session, "isolation_a", "primary", patient_id=patient_a, tenant_id=tenant_id, icd10_code="C34.90")
    _seed_diagnosis(db_session, "isolation_b", "primary", patient_id=patient_b, tenant_id=tenant_id, icd10_code="I50.9")

    bundle_a = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_a, tenant_id=tenant_id)
    codes_a = {item.observed_value for item in bundle_a.by_concept_code("DIAGNOSIS")}
    assert codes_a == {"C34.90"}


def test_patient_not_found_raises_typed_error(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    with pytest.raises(PatientNotFoundError):
        ClinicalEvidenceHarvester().harvest(db_session, patient_id=uuid.uuid4(), tenant_id=tenant_id)


def test_cross_tenant_actor_context_is_rejected(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "cross_tenant", tenant_id)

    from app.services.eligibility.clinical_evidence_harvester import ActorContext

    other_tenant_id = uuid.uuid4()
    with pytest.raises(CrossTenantAccessError):
        ClinicalEvidenceHarvester().harvest(
            db_session,
            patient_id=patient_id,
            tenant_id=tenant_id,
            actor_context=ActorContext(tenant_id=other_tenant_id),
        )


def test_patient_in_different_tenant_is_not_found(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "wrong_tenant_lookup", tenant_id)

    other_tenant_id = uuid.uuid4()
    if db_session.get(Tenant, other_tenant_id) is None:
        db_session.add(Tenant(id=other_tenant_id, legal_name="Other Hospice", display_name="Other", npi="9999999999"))
        db_session.commit()

    with pytest.raises(PatientNotFoundError):
        ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=other_tenant_id)

    db_session.query(Tenant).filter(Tenant.id == other_tenant_id).delete()
    db_session.commit()


def test_rerun_produces_identical_evidence_identities(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "deterministic", tenant_id)
    _seed_diagnosis(db_session, "deterministic", "primary", patient_id=patient_id, tenant_id=tenant_id)

    bundle_1 = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id)
    bundle_2 = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id)

    ids_1 = [item.evidence_id for item in bundle_1.items]
    ids_2 = [item.evidence_id for item in bundle_2.items]
    assert ids_1 == ids_2


def test_multiple_diagnoses_ordered_deterministically(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "ordering", tenant_id)
    _seed_diagnosis(
        db_session, "ordering", "second", patient_id=patient_id, tenant_id=tenant_id,
        diagnosis_type="SECONDARY", icd10_code="I50.9", diagnosis_description="Heart failure",
        display_name="Heart failure", effective_date=date(2025, 2, 1),
    )
    _seed_diagnosis(
        db_session, "ordering", "first", patient_id=patient_id, tenant_id=tenant_id,
        diagnosis_type="PRIMARY", icd10_code="C34.90", effective_date=date(2025, 1, 1),
    )

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id)
    codes = [item.observed_value for item in bundle.by_concept_code("DIAGNOSIS")]
    assert codes == ["C34.90", "I50.9"]  # ordered by effective_date ascending


def test_harvester_draws_no_clinical_conclusion(db_session):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient_id = _seed_patient(db_session, "no_conclusion", tenant_id)
    _seed_diagnosis(db_session, "no_conclusion", "primary", patient_id=patient_id, tenant_id=tenant_id)

    bundle = ClinicalEvidenceHarvester().harvest(db_session, patient_id=patient_id, tenant_id=tenant_id)
    forbidden_terms = {"eligible", "eligibility", "certification", "recertification", "prognosis", "discharge"}
    for item in bundle.items:
        payload_fields = set(vars(item).keys())
        for field_name in payload_fields:
            assert not any(term in field_name.lower() for term in forbidden_terms)
