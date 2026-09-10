"""
Priority 5 -- Contracted Status Workflow / Authorization Workflow
readiness consumption (contracted_authorization_workflow_service.py).

Verifies:
- pure evaluate_contracted_status_readiness severity mapping
  (YES -> no finding, NO -> warning, UNKNOWN/None -> warning)
- evaluate_authorization_readiness severity mapping, including the DB
  evidence lookup (AUTHORIZATION_DOCUMENT / NON_AUTH_VERIFICATION)
- check_patient_billing_readiness folds both findings in as read-only
  consumption, without owning or writing PatientFaceSheet.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.billing.services.billing_readiness_service import check_patient_billing_readiness
from app.billing.services.contracted_authorization_workflow_service import (
    authorization_required_status_label,
    contracted_status_label,
    evaluate_authorization_readiness,
    evaluate_contracted_status_readiness,
)
from app.billing.services.eligibility_workflow_service import record_eligibility_source_document
from app.models.patient_facesheet import PatientFaceSheet

from tests.test_billing_readiness_service import _fully_ready_patient
from tests.test_eligibility_workflow_service import _make_document_record, _make_user


def _set_payer_review(
    db_session, tenant_id: str, patient_id, *, contracted_status=None, authorization_required_status=None
) -> None:
    actor_id = _make_user(db_session, tenant_id)
    facesheet = PatientFaceSheet(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        patient_id=patient_id,
        first_name="Payer",
        last_name="Review",
        contracted_status=contracted_status,
        authorization_required_status=authorization_required_status,
        created_by=actor_id,
    )
    db_session.add(facesheet)
    db_session.commit()


class TestPureSeverityMapping:
    def test_contracted_yes_is_no_finding(self):
        finding = evaluate_contracted_status_readiness(contracted_status="YES")
        assert finding.blockers == []
        assert finding.warnings == []

    def test_contracted_no_is_warning_not_blocker(self):
        finding = evaluate_contracted_status_readiness(contracted_status="NO")
        assert finding.blockers == []
        assert len(finding.warnings) == 1

    @pytest.mark.parametrize("value", ["UNKNOWN", None])
    def test_contracted_unknown_or_absent_is_warning(self, value):
        finding = evaluate_contracted_status_readiness(contracted_status=value)
        assert finding.blockers == []
        assert len(finding.warnings) == 1

    def test_display_labels(self):
        assert contracted_status_label("YES") == "Contracted"
        assert contracted_status_label("NO") == "Not Contracted"
        assert contracted_status_label("UNKNOWN") == "Unknown"
        assert contracted_status_label(None) == "Unknown"
        assert authorization_required_status_label("YES") == "Authorization Required"
        assert authorization_required_status_label("NO") == "Authorization Not Required"
        assert authorization_required_status_label(None) == "Unknown"


class TestAuthorizationReadinessEvidenceLookup:
    def test_required_yes_no_evidence_is_blocker(self, db_session, tenant):
        patient = _fully_ready_patient(db_session, tenant.id, mrn="MRN-AUTH-1")

        finding = evaluate_authorization_readiness(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            authorization_required_status="YES",
        )
        assert len(finding.blockers) == 1
        assert finding.warnings == []

    def test_required_yes_with_evidence_is_no_finding(self, db_session, tenant):
        patient = _fully_ready_patient(db_session, tenant.id, mrn="MRN-AUTH-2")
        user_id = _make_user(db_session, tenant.id)
        doc_record = _make_document_record(db_session, tenant.id, patient, user_id)
        record_eligibility_source_document(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            document_record_id=str(doc_record.id),
            document_type="AUTHORIZATION_DOCUMENT",
            uploaded_by_user_id=str(user_id),
        )

        finding = evaluate_authorization_readiness(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            authorization_required_status="YES",
        )
        assert finding.blockers == []
        assert finding.warnings == []

    def test_required_no_without_verification_is_warning_not_blocker(self, db_session, tenant):
        patient = _fully_ready_patient(db_session, tenant.id, mrn="MRN-AUTH-3")

        finding = evaluate_authorization_readiness(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            authorization_required_status="NO",
        )
        assert finding.blockers == []
        assert len(finding.warnings) == 1

    def test_required_no_with_verification_is_no_finding(self, db_session, tenant):
        patient = _fully_ready_patient(db_session, tenant.id, mrn="MRN-AUTH-4")
        user_id = _make_user(db_session, tenant.id)
        doc_record = _make_document_record(db_session, tenant.id, patient, user_id)
        record_eligibility_source_document(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            document_record_id=str(doc_record.id),
            document_type="NON_AUTH_VERIFICATION",
            uploaded_by_user_id=str(user_id),
        )

        finding = evaluate_authorization_readiness(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            authorization_required_status="NO",
        )
        assert finding.blockers == []
        assert finding.warnings == []

    def test_required_unknown_is_warning(self, db_session, tenant):
        patient = _fully_ready_patient(db_session, tenant.id, mrn="MRN-AUTH-5")

        finding = evaluate_authorization_readiness(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            authorization_required_status="UNKNOWN",
        )
        assert finding.blockers == []
        assert len(finding.warnings) == 1


class TestBillingReadinessConsumesPayerReview:
    SERVICE_DATE = date(2026, 3, 15)

    def test_no_facesheet_row_has_no_effect(self, db_session, tenant):
        # Non-regression: a patient with no PatientFaceSheet row at all
        # (pre-existing/legacy fixture) must remain unaffected -- absent
        # data is never treated as a negative finding.
        patient = _fully_ready_patient(db_session, tenant.id, mrn="MRN-READY-NOFS")

        result = check_patient_billing_readiness(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            service_date=self.SERVICE_DATE,
        )
        assert result.ready is True
        assert result.blockers == []

    def test_authorization_required_no_evidence_blocks_readiness(self, db_session, tenant):
        patient = _fully_ready_patient(db_session, tenant.id, mrn="MRN-READY-AUTHBLK")
        _set_payer_review(
            db_session,
            tenant.id,
            patient.id,
            contracted_status="YES",
            authorization_required_status="YES",
        )

        result = check_patient_billing_readiness(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            service_date=self.SERVICE_DATE,
        )
        assert result.ready is False
        assert any("authorization evidence" in b for b in result.blockers)

    def test_contracted_no_is_at_risk_not_blocked(self, db_session, tenant):
        patient = _fully_ready_patient(db_session, tenant.id, mrn="MRN-READY-NOTCONTR")
        _set_payer_review(
            db_session,
            tenant.id,
            patient.id,
            contracted_status="NO",
            authorization_required_status="NO",
        )

        result = check_patient_billing_readiness(
            db_session,
            tenant_id=tenant.id,
            patient_id=str(patient.id),
            service_date=self.SERVICE_DATE,
        )
        # NO Contracted + NO Authorization-Required-without-verification are
        # both warnings, never blockers -- patient remains "ready" (no hard
        # blockers) though a caller deriving AT_RISK from warnings would
        # surface both. A third warning (Priority 6: missing election/
        # consent documentation, since _fully_ready_patient has none) is
        # also expected here -- also never a blocker.
        assert result.ready is True
        assert result.blockers == []
        assert len(result.warnings) == 3
