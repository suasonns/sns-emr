"""
Priority 6 -- Election / Consent Document Workflow readiness consumption
(election_consent_workflow_service.py).

Verifies:
- has_election_consent_evidence() / evaluate_election_consent_readiness()
  treat ANY ACTIVE DocumentRecord of the 8 election/consent document
  types as satisfying the requirement.
- Missing election/consent documentation is ALWAYS a warning, NEVER a
  blocker -- this must never regress into blocking admission, SOC, or
  billing readiness.
- check_patient_billing_readiness folds this finding in as read-only
  consumption of the Document Registry (DocumentRecord), never writing
  to it and never introducing a second "consent status" field.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.billing.services.billing_readiness_service import check_patient_billing_readiness
from app.billing.services.election_consent_workflow_service import (
    ELECTION_CONSENT_DOCUMENT_TYPES,
    evaluate_election_consent_readiness,
    has_election_consent_evidence,
)
from app.models.document_record import DocumentRecord

from tests.test_billing_readiness_service import _fully_ready_patient
from tests.test_eligibility_workflow_service import _make_user

SERVICE_DATE = date(2026, 3, 15)


def _make_document(db_session, tenant_id, patient, user_id, *, document_type, lifecycle_status="ACTIVE"):
    doc = DocumentRecord(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        patient_id=patient.id,
        document_type=document_type,
        source="EXTERNAL",
        file_name=f"{document_type.lower()}.pdf",
        uploaded_by=user_id,
        created_by=user_id,
        lifecycle_status=lifecycle_status,
    )
    db_session.add(doc)
    db_session.commit()
    return doc


class TestElectionConsentEvidenceLookup:
    def test_no_documents_means_no_evidence(self, db_session, tenant):
        patient = _fully_ready_patient(db_session, tenant.id, mrn="MRN-CONSENT-1")

        assert has_election_consent_evidence(
            db_session, tenant_id=tenant.id, patient_id=str(patient.id)
        ) is False

    @pytest.mark.parametrize("document_type", sorted(ELECTION_CONSENT_DOCUMENT_TYPES))
    def test_any_election_consent_type_counts_as_evidence(self, db_session, tenant, document_type):
        patient = _fully_ready_patient(db_session, tenant.id, mrn=f"MRN-CONSENT-{document_type[:8]}")
        user_id = _make_user(db_session, tenant.id)
        _make_document(db_session, tenant.id, patient, user_id, document_type=document_type)

        assert has_election_consent_evidence(
            db_session, tenant_id=tenant.id, patient_id=str(patient.id)
        ) is True

    def test_archived_document_does_not_count(self, db_session, tenant):
        patient = _fully_ready_patient(db_session, tenant.id, mrn="MRN-CONSENT-ARCHIVED")
        user_id = _make_user(db_session, tenant.id)
        _make_document(
            db_session,
            tenant.id,
            patient,
            user_id,
            document_type="CONSENT_FORM",
            lifecycle_status="ARCHIVED",
        )

        assert has_election_consent_evidence(
            db_session, tenant_id=tenant.id, patient_id=str(patient.id)
        ) is False

    def test_unrelated_document_type_does_not_count(self, db_session, tenant):
        patient = _fully_ready_patient(db_session, tenant.id, mrn="MRN-CONSENT-UNRELATED")
        user_id = _make_user(db_session, tenant.id)
        _make_document(db_session, tenant.id, patient, user_id, document_type="PLAN_OF_CARE")

        assert has_election_consent_evidence(
            db_session, tenant_id=tenant.id, patient_id=str(patient.id)
        ) is False


class TestEvaluateElectionConsentReadinessIsNeverABlocker:
    def test_missing_is_warning_only(self, db_session, tenant):
        patient = _fully_ready_patient(db_session, tenant.id, mrn="MRN-CONSENT-WARN")

        finding = evaluate_election_consent_readiness(
            db_session, tenant_id=tenant.id, patient_id=str(patient.id)
        )
        assert finding.blockers == []
        assert len(finding.warnings) == 1

    def test_present_is_no_finding(self, db_session, tenant):
        patient = _fully_ready_patient(db_session, tenant.id, mrn="MRN-CONSENT-CLEAR")
        user_id = _make_user(db_session, tenant.id)
        _make_document(db_session, tenant.id, patient, user_id, document_type="ELECTION_STATEMENT")

        finding = evaluate_election_consent_readiness(
            db_session, tenant_id=tenant.id, patient_id=str(patient.id)
        )
        assert finding.blockers == []
        assert finding.warnings == []


class TestBillingReadinessConsumesElectionConsent:
    def test_missing_consent_is_at_risk_not_blocked(self, db_session, tenant):
        patient = _fully_ready_patient(db_session, tenant.id, mrn="MRN-CONSENT-READY-MISSING")

        result = check_patient_billing_readiness(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            service_date=SERVICE_DATE,
        )
        # Never a blocker -- patient remains "ready" (no hard blockers)
        # even with no election/consent documentation on file.
        assert result.ready is True
        assert result.blockers == []
        assert len(result.warnings) == 1

    def test_present_consent_has_no_effect_on_readiness(self, db_session, tenant):
        patient = _fully_ready_patient(db_session, tenant.id, mrn="MRN-CONSENT-READY-PRESENT")
        user_id = _make_user(db_session, tenant.id)
        _make_document(db_session, tenant.id, patient, user_id, document_type="HIPAA_ACKNOWLEDGEMENT")

        result = check_patient_billing_readiness(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            service_date=SERVICE_DATE,
        )
        assert result.ready is True
        assert result.blockers == []
        assert result.warnings == []
