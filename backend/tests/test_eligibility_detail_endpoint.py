"""
Tests for GET /billing/eligibility-detail/{patient_id} (Directive item
12, Phase 7 -- read-only eligibility detail view): verification history,
benefit-period determination history, source documents, and admission
gate status, sourced directly from the Phases 1-4 tables.
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
from app.models.user import User

from tests.test_aging_report_service import _enable_billing_for_tenant, _headers
from tests.test_billing_readiness_service import _make_patient


def _billing_tenant(db_session):
    tenant_id = uuid.uuid4()
    return _enable_billing_for_tenant(
        db_session, tenant_id, legal_name=f"Eligibility Detail Test Agency {tenant_id.hex[:8]}"
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


class TestEligibilityDetailEndpoint:
    def test_404_for_unknown_patient(self, db_session, client):
        billing_tenant = _billing_tenant(db_session)
        tenant_id = billing_tenant.id
        response = client.get(
            f"/billing/eligibility-detail/{uuid.uuid4()}",
            headers=_headers("BILLING", tenant_id),
            params={"tenant_id": str(tenant_id)},
        )
        assert response.status_code == 404

    def test_detail_returns_empty_histories_when_no_rows_exist(self, db_session, client):
        billing_tenant = _billing_tenant(db_session)
        tenant_id = billing_tenant.id
        patient = _make_patient(db_session, str(tenant_id), mrn="MRN-DETAIL-1")

        response = client.get(
            f"/billing/eligibility-detail/{patient.id}",
            headers=_headers("BILLING", tenant_id),
            params={"tenant_id": str(tenant_id)},
        )

        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["patient_id"] == str(patient.id)
        assert payload["mrn"] == patient.mrn
        assert payload["admission_gate_status"] == "CLEAR"
        assert payload["verification_history"] == []
        assert payload["benefit_period_determination_history"] == []
        assert payload["source_documents"] == []

    def test_detail_returns_full_history_newest_first(self, db_session, client):
        billing_tenant = _billing_tenant(db_session)
        tenant_id = billing_tenant.id
        patient = _make_patient(db_session, str(tenant_id), mrn="MRN-DETAIL-2")
        user_id = _make_user(db_session, tenant_id)

        doc1 = DocumentRecord(
            id=uuid.uuid4(), tenant_id=uuid.UUID(str(tenant_id)), patient_id=patient.id,
            document_type="MEDICARE_BENEFICIARY_ELIGIBILITY_REPORT", source="EXTERNAL", uploaded_by=user_id,
        )
        doc2 = DocumentRecord(
            id=uuid.uuid4(), tenant_id=uuid.UUID(str(tenant_id)), patient_id=patient.id,
            document_type="MEDICARE_BENEFICIARY_ELIGIBILITY_REPORT", source="EXTERNAL", uploaded_by=user_id,
        )
        db_session.add_all([doc1, doc2])
        db_session.commit()

        esd1 = record_eligibility_source_document(
            db_session, tenant_id=str(tenant_id), patient_id=str(patient.id),
            document_record_id=str(doc1.id), document_type="MEDICARE_BENEFICIARY_ELIGIBILITY_REPORT",
            uploaded_by_user_id=str(user_id),
        )
        esd2 = record_eligibility_source_document(
            db_session, tenant_id=str(tenant_id), patient_id=str(patient.id),
            document_record_id=str(doc2.id), document_type="MEDICARE_BENEFICIARY_ELIGIBILITY_REPORT",
            uploaded_by_user_id=str(user_id), supersedes_document_id=str(esd1.id),
        )

        record_eligibility_verification(
            db_session, tenant_id=str(tenant_id), patient_id=str(patient.id),
            source_document_id=str(esd1.id), verified_by_user_id=str(user_id), status="VERIFIED_ACTIVE",
        )
        record_eligibility_verification(
            db_session, tenant_id=str(tenant_id), patient_id=str(patient.id),
            source_document_id=str(esd2.id), verified_by_user_id=str(user_id), status="VERIFIED_ACTIVE",
        )

        record_benefit_period_determination(
            db_session, tenant_id=str(tenant_id), patient_id=str(patient.id),
            determination_status="INFORMATION_INCOMPLETE",
        )
        record_benefit_period_determination(
            db_session, tenant_id=str(tenant_id), patient_id=str(patient.id),
            determination_status="BENEFIT_PERIOD_CONFIRMED", anticipated_benefit_period_number=1,
        )

        response = client.get(
            f"/billing/eligibility-detail/{patient.id}",
            headers=_headers("BILLING", tenant_id),
            params={"tenant_id": str(tenant_id)},
        )

        assert response.status_code == 200, response.text
        payload = response.json()
        assert len(payload["verification_history"]) == 2
        assert len(payload["benefit_period_determination_history"]) == 2
        assert len(payload["source_documents"]) == 2

        # Newest-first: the most recent determination is CONFIRMED, not
        # the superseded INFORMATION_INCOMPLETE one.
        assert payload["benefit_period_determination_history"][0]["determination_status"] == "BENEFIT_PERIOD_CONFIRMED"
        assert payload["benefit_period_determination_history"][1]["determination_status"] == "INFORMATION_INCOMPLETE"

        # The original document is marked superseded, never deleted.
        superseded_doc = next(d for d in payload["source_documents"] if d["id"] == str(esd1.id))
        assert superseded_doc["status"] == "SUPERSEDED"

        # Admission gate now CLEAR since the latest determination is confirmed.
        assert payload["admission_gate_status"] == "CLEAR"
