"""
Verifies the fix for a real, verified production defect: the
`diagnosis_recommendations` table (and its optional
`diagnosis_recommendation_reasoning_links` join table) referenced by
`app/services/reasoning_result_to_recommendation_service.py` via raw SQL had
no Alembic migration. Every call to
`clinical_reasoning_bridge.run_clinical_reasoning()` -- which fires on RN/LVN
visit finalize, MSW/SC ICA lock, MD/NP F2F finalize, and Certification (CTI)
signing -- reaches `ReasoningResultToRecommendationService.generate_for_patient()`,
which previously raised `psycopg2.errors.UndefinedTable` the moment a
`clinical_reasoning_results` row had a non-null `recommended_icd10` (confirmed
against the dev DB before the fix: the table did not exist at all).

Migration `e0babf84fd5e_add_diagnosis_recommendations_table` adds the missing
tables using the exact column list the raw-SQL INSERT/SELECT statements
already assumed. This test exercises the real service end-to-end against a
real `clinical_reasoning_results` row and asserts:

1. No exception is raised (the actual regression).
2. Exactly one `diagnosis_recommendations` row is created, in
   PENDING_REVIEW / PROPOSED state (never auto-accepted).
3. Rerunning is idempotent -- no duplicate row for the same
   (patient, icd10, diagnosis) group.
4. The service never writes `patient_diagnoses` -- confirming the
   "recommendation only, does not replace MD/RN review" contract documented
   on `ReasoningResultToRecommendationService`.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import text

from app.models.icd10_master import ICD10Master
from app.models.patient import Patient
from app.models.patient_diagnosis import PatientDiagnosis
from app.services.reasoning_result_to_recommendation_service import (
    ReasoningResultToRecommendationService,
)


def _make_patient(db_session, tenant_id: str) -> Patient:
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(tenant_id),
        mrn=f"DXREC-{uuid.uuid4().hex[:10]}",
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="Systolic heart failure, chronic",
        status="ACTIVE",
        admission_status="ADMITTED",
    )
    db_session.add(patient)
    db_session.flush()
    return patient


def _ensure_icd10_seed(db_session) -> None:
    existing = (
        db_session.query(ICD10Master)
        .filter(ICD10Master.icd10_code == "I5022")
        .first()
    )
    if existing:
        return
    db_session.add(
        ICD10Master(
            icd10_code="I5022",
            diagnosis_description="Chronic systolic (congestive) heart failure",
            display_name="Chronic systolic (congestive) heart failure",
            billable=True,
            active=True,
        )
    )
    db_session.flush()


def _insert_reasoning_result(db_session, *, tenant_id, patient_id) -> uuid.UUID:
    result_id = uuid.uuid4()
    db_session.execute(
        text(
            """
            INSERT INTO clinical_reasoning_results (
                id, tenant_id, patient_id, source_document_id,
                source_document_name, profile_key, interpretation_key,
                reasoning_category, severity_level, confidence,
                matched_evidence, missing_evidence, evidence_count,
                rationale, clinical_summary, recommended_diagnosis,
                recommended_icd10, requires_rn_review, requires_md_review,
                requires_idg_review, reasoning_version, created_at
            ) VALUES (
                :id, :tenant_id, :patient_id, NULL,
                NULL, 'cardiac_decline', 'chf_progression',
                'cardiac', 'high', 'high',
                '{}', '{}', 3,
                'Documented decline supports this diagnosis as driver',
                'Progressive decline with documented trend',
                'TEST DRIVER DIAGNOSIS', 'I50.22',
                true, true, false, 'test-v1', :created_at
            )
            """
        ),
        {
            "id": result_id,
            "tenant_id": tenant_id,
            "patient_id": patient_id,
            "created_at": datetime.now(timezone.utc),
        },
    )
    db_session.flush()
    return result_id


def test_generate_for_patient_creates_recommendation_without_crashing(db_session, tenant):
    _ensure_icd10_seed(db_session)
    patient = _make_patient(db_session, tenant.id)
    _insert_reasoning_result(db_session, tenant_id=uuid.UUID(tenant.id), patient_id=patient.id)

    service = ReasoningResultToRecommendationService()

    # This is the exact call made by clinical_reasoning_bridge.run_clinical_reasoning()
    # after every visit/F2F/certification finalize -- previously raised
    # UndefinedTable before the migration fix.
    result = service.generate_for_patient(
        db=db_session,
        tenant_id=uuid.UUID(tenant.id),
        patient_id=patient.id,
        commit=False,
    )

    assert result["recommendations_created"] == 1, result["skipped_groups"]
    assert len(result["created_recommendation_ids"]) == 1

    row = db_session.execute(
        text(
            "SELECT recommendation_status, recommended_status, is_terminal_candidate, "
            "requires_md_review, diagnosis_keyword, promoted_patient_diagnosis_id "
            "FROM diagnosis_recommendations WHERE patient_id = :patient_id"
        ),
        {"patient_id": patient.id},
    ).mappings().one()

    assert row["recommendation_status"] == "PENDING_REVIEW"
    assert row["recommended_status"] == "PROPOSED"
    assert row["is_terminal_candidate"] is True
    assert row["requires_md_review"] is True
    assert row["promoted_patient_diagnosis_id"] is None

    # Recommendation-only: no patient_diagnoses row was created/touched by
    # the recommendation service.
    patient_diagnosis_count = (
        db_session.query(PatientDiagnosis)
        .filter(PatientDiagnosis.patient_id == patient.id)
        .count()
    )
    assert patient_diagnosis_count == 0


def test_generate_for_patient_is_idempotent(db_session, tenant):
    _ensure_icd10_seed(db_session)
    patient = _make_patient(db_session, tenant.id)
    _insert_reasoning_result(db_session, tenant_id=uuid.UUID(tenant.id), patient_id=patient.id)

    service = ReasoningResultToRecommendationService()

    first = service.generate_for_patient(
        db=db_session, tenant_id=uuid.UUID(tenant.id), patient_id=patient.id, commit=False,
    )
    second = service.generate_for_patient(
        db=db_session, tenant_id=uuid.UUID(tenant.id), patient_id=patient.id, commit=False,
    )

    assert first["recommendations_created"] == 1
    assert second["recommendations_created"] == 0
    assert second["skipped_groups"][0]["reason"] == "RECOMMENDATION_ALREADY_EXISTS"

    total = db_session.execute(
        text("SELECT count(*) FROM diagnosis_recommendations WHERE patient_id = :patient_id"),
        {"patient_id": patient.id},
    ).scalar_one()
    assert total == 1
