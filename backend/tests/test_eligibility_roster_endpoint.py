"""
Tests for the enriched GET /billing/eligibility-roster endpoint
(Directive item 12 -- biller eligibility workspace, Phase 5): confirms
the additive structured-eligibility/benefit-period/admission-gate fields
are present and correct alongside the pre-existing legacy
PatientInsurance.eligibility_status field, which must remain unchanged
for backward compatibility.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.billing.services.eligibility_workflow_service import (
    record_benefit_period_determination,
    record_eligibility_source_document,
    record_eligibility_verification,
)
from app.models.document_record import DocumentRecord
from app.models.patient_insurance import PatientInsurance
from app.models.user import User

from tests.test_aging_report_service import _enable_billing_for_tenant, _headers
from tests.test_billing_readiness_service import _make_patient


def _billing_tenant(db_session):
    tenant_id = uuid.uuid4()
    return _enable_billing_for_tenant(
        db_session, tenant_id, legal_name=f"Eligibility Roster Test Agency {tenant_id.hex[:8]}"
    )


def _make_user(db_session, tenant_id, *, role: str = "BILLING") -> uuid.UUID:
    user_id = uuid.uuid4()
    db_session.add(
        User(
            id=user_id,
            tenant_id=uuid.UUID(str(tenant_id)),
            email=f"{user_id.hex[:8]}@example.com",
            full_name="Test Biller",
            role=role,
        )
    )
    db_session.commit()
    return user_id


def _make_insurance(db_session, tenant_id, patient) -> PatientInsurance:
    insurance = PatientInsurance(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(str(tenant_id)),
        patient_id=patient.id,
        payer_type="MEDICARE",
        payer_name="Medicare Part A/B",
        subscriber_id="1EG4TE5MK73",
        priority_order=1,
        is_active=True,
        effective_date=date(2020, 1, 1),
        eligibility_status="ACTIVE",
    )
    db_session.add(insurance)
    db_session.commit()
    return insurance


class TestEligibilityRosterEnrichment:
    def test_roster_row_has_no_structured_fields_when_no_rows_exist(self, db_session, client):
        billing_tenant = _billing_tenant(db_session)
        tenant_id = billing_tenant.id
        patient = _make_patient(db_session, str(tenant_id), mrn="MRN-ROSTER-1")
        _make_insurance(db_session, tenant_id, patient)

        response = client.get(
            "/billing/eligibility-roster",
            headers=_headers("BILLING", tenant_id),
            params={"tenant_id": str(tenant_id)},
        )

        assert response.status_code == 200, response.text
        payload = response.json()
        row = next(r for r in payload["roster"] if r["patient_id"] == str(patient.id))
        # Legacy field untouched.
        assert row["eligibility_status"] == "ACTIVE"
        # New structured fields are explicitly None/CLEAR, not fabricated.
        assert row["payer_eligibility_verification_status"] is None
        assert row["benefit_period_determination_status"] is None
        assert row["admission_gate_status"] == "CLEAR"
        assert row["action_required"] is None

    def test_roster_row_surfaces_admission_gate_when_unresolved(self, db_session, client):
        billing_tenant = _billing_tenant(db_session)
        tenant_id = billing_tenant.id
        patient = _make_patient(db_session, str(tenant_id), mrn="MRN-ROSTER-2")
        _make_insurance(db_session, tenant_id, patient)
        user_id = _make_user(db_session, tenant_id)

        doc_record = DocumentRecord(
            id=uuid.uuid4(),
            tenant_id=uuid.UUID(str(tenant_id)),
            patient_id=patient.id,
            document_type="MEDICARE_BENEFICIARY_ELIGIBILITY_REPORT",
            source="EXTERNAL",
            uploaded_by=user_id,
        )
        db_session.add(doc_record)
        db_session.commit()

        esd = record_eligibility_source_document(
            db_session,
            tenant_id=str(tenant_id),
            patient_id=str(patient.id),
            document_record_id=str(doc_record.id),
            document_type="MEDICARE_BENEFICIARY_ELIGIBILITY_REPORT",
            uploaded_by_user_id=str(user_id),
        )
        record_eligibility_verification(
            db_session,
            tenant_id=str(tenant_id),
            patient_id=str(patient.id),
            source_document_id=str(esd.id),
            verified_by_user_id=str(user_id),
            status="REVIEW_REQUIRED",
        )
        record_benefit_period_determination(
            db_session,
            tenant_id=str(tenant_id),
            patient_id=str(patient.id),
            determination_status="BENEFIT_PERIOD_CONFIRMED",
            anticipated_benefit_period_number=1,
        )

        response = client.get(
            "/billing/eligibility-roster",
            headers=_headers("BILLING", tenant_id),
            params={"tenant_id": str(tenant_id)},
        )

        assert response.status_code == 200, response.text
        payload = response.json()
        row = next(r for r in payload["roster"] if r["patient_id"] == str(patient.id))
        assert row["payer_eligibility_verification_status"] == "REVIEW_REQUIRED"
        assert row["benefit_period_determination_status"] == "BENEFIT_PERIOD_CONFIRMED"
        assert row["anticipated_benefit_period_number"] == 1
        assert row["admission_gate_status"] == "ADMISSION_REVIEW_REQUIRED"
        assert row["action_required"] is not None
