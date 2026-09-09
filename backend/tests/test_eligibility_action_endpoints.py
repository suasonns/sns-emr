"""
Tests for the Phase A-E eligibility action workflow endpoints
(backend/app/billing/api/eligibility_action_router.py):
  - Phase A: document upload + versioning (supersession)
  - Phase B: verification creation / reverification
  - Phase D: RN review actions (approve/reject/clarify/F2F/hold-release)
  - Phase E: escalate / document-review-request / billing note
  - Phase C: eligibility change impact engine (billing-readiness
    re-evaluation triggered only for ADMITTED patients)
  - Deliverable 9: every action above lands in the shared
    ReadinessWorkflowEvent audit trail, surfaced through the existing
    GET /billing/readiness-history/{patient_id} endpoint.
"""

from __future__ import annotations

import io
import uuid

import pytest
from pypdf import PdfWriter

from app.billing.models.billing_readiness_verdict import BillingReadinessVerdict
from app.billing.models.eligibility_source_document import EligibilitySourceDocument
from app.billing.models.readiness_follow_up import ReadinessFollowUp
from app.billing.services.eligibility_workflow_service import (
    record_eligibility_source_document,
    record_eligibility_verification,
)
from app.models.document_record import DocumentRecord
from app.models.user import User
from app.services.document_storage import get_document_storage

from tests.test_aging_report_service import _enable_billing_for_tenant, _headers
from tests.test_billing_readiness_service import (
    _make_admitted,
    _make_benefit_period,
    _make_certification,
    _make_patient,
    _make_payer,
)


def _billing_tenant(db_session):
    tenant_id = uuid.uuid4()
    return _enable_billing_for_tenant(
        db_session, tenant_id, legal_name=f"Eligibility Action Test Agency {tenant_id.hex[:8]}"
    )


def _minimal_pdf_bytes() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


@pytest.fixture()
def document_storage_env(monkeypatch, tmp_path):
    monkeypatch.setenv("DOCUMENT_STORAGE_PROVIDER", "local")
    monkeypatch.setenv("DOCUMENT_STORAGE_DIR", str(tmp_path))
    monkeypatch.setenv("DOCUMENT_MAX_UPLOAD_BYTES", "1048576")
    get_document_storage.cache_clear()
    try:
        yield tmp_path
    finally:
        get_document_storage.cache_clear()


def _ready_admitted_patient(db_session, tenant_id, *, mrn):
    """A minimally-ready ADMITTED patient -- enough for
    check_patient_billing_readiness to persist a READY verdict, so Phase
    C tests can assert billing_readiness_reevaluated=True with a real
    readiness_status back."""
    patient = _make_patient(db_session, str(tenant_id), mrn=mrn)
    _make_admitted(db_session, str(tenant_id), patient)
    bp = _make_benefit_period(db_session, str(tenant_id), patient)
    _make_certification(db_session, str(tenant_id), patient, bp)
    _make_payer(db_session, patient)
    return patient


class TestPhaseADocumentUpload:
    def test_upload_creates_version_1_document(self, db_session, client, document_storage_env):
        tenant = _billing_tenant(db_session)
        patient = _make_patient(db_session, str(tenant.id), mrn="MRN-UPLOAD-1")

        response = client.post(
            f"/billing/eligibility/{patient.id}/documents",
            headers=_headers("BILLING", tenant.id),
            params={"tenant_id": str(tenant.id)},
            data={
                "document_type": "PAYER_ELIGIBILITY_RESPONSE",
                "notes": "Initial portal eligibility check",
            },
            files={"file": ("eligibility.pdf", _minimal_pdf_bytes(), "application/pdf")},
        )

        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["version"] == 1
        assert payload["status"] == "ACTIVE"
        assert payload["supersedes_document_id"] is None
        assert payload["notes"] == "Initial portal eligibility check"

        stored = db_session.get(EligibilitySourceDocument, uuid.UUID(payload["id"]))
        assert stored is not None
        assert stored.version == 1

    def test_upload_with_supersedes_creates_version_2_and_supersedes_prior(
        self, db_session, client, document_storage_env
    ):
        tenant = _billing_tenant(db_session)
        patient = _make_patient(db_session, str(tenant.id), mrn="MRN-UPLOAD-2")

        first = client.post(
            f"/billing/eligibility/{patient.id}/documents",
            headers=_headers("BILLING", tenant.id),
            params={"tenant_id": str(tenant.id)},
            data={"document_type": "PAYER_ELIGIBILITY_RESPONSE"},
            files={"file": ("v1.pdf", _minimal_pdf_bytes(), "application/pdf")},
        )
        assert first.status_code == 200, first.text
        first_id = first.json()["id"]

        second = client.post(
            f"/billing/eligibility/{patient.id}/documents",
            headers=_headers("BILLING", tenant.id),
            params={"tenant_id": str(tenant.id)},
            data={
                "document_type": "PAYER_ELIGIBILITY_RESPONSE",
                "supersedes_document_id": first_id,
                "notes": "Updated coverage report",
            },
            files={"file": ("v2.pdf", _minimal_pdf_bytes(), "application/pdf")},
        )
        assert second.status_code == 200, second.text
        second_payload = second.json()
        assert second_payload["version"] == 2
        assert second_payload["supersedes_document_id"] == first_id

        prior = db_session.get(EligibilitySourceDocument, uuid.UUID(first_id))
        db_session.refresh(prior)
        assert prior.status == "SUPERSEDED"

    def test_upload_rejects_unknown_document_type(self, db_session, client, document_storage_env):
        tenant = _billing_tenant(db_session)
        patient = _make_patient(db_session, str(tenant.id), mrn="MRN-UPLOAD-3")

        response = client.post(
            f"/billing/eligibility/{patient.id}/documents",
            headers=_headers("BILLING", tenant.id),
            params={"tenant_id": str(tenant.id)},
            data={"document_type": "NOT_A_REAL_TYPE"},
            files={"file": ("x.pdf", _minimal_pdf_bytes(), "application/pdf")},
        )
        assert response.status_code == 400


class TestPhaseBReverification:
    def _make_source_document(self, db_session, tenant, patient):
        user_id = db_session.get(User, uuid.UUID("11111111-1111-1111-1111-111111111111")).id
        doc = DocumentRecord(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            patient_id=patient.id,
            document_type="PAYER_ELIGIBILITY_RESPONSE",
            source="ELIGIBILITY",
            uploaded_by=user_id,
        )
        db_session.add(doc)
        db_session.commit()
        return record_eligibility_source_document(
            db_session,
            tenant_id=str(tenant.id),
            patient_id=str(patient.id),
            document_record_id=str(doc.id),
            document_type="PAYER_ELIGIBILITY_RESPONSE",
            uploaded_by_user_id=str(user_id),
        )

    def test_first_verification_is_created_not_reverified(self, db_session, client):
        tenant = _billing_tenant(db_session)
        patient = _make_patient(db_session, str(tenant.id), mrn="MRN-VERIFY-1")
        source_doc = self._make_source_document(db_session, tenant, patient)

        response = client.post(
            f"/billing/eligibility/{patient.id}/verifications",
            headers=_headers("BILLING", tenant.id),
            json={
                "tenant_id": str(tenant.id),
                "source_document_id": str(source_doc.id),
                "status": "VERIFIED_ACTIVE",
            },
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["status"] == "VERIFIED_ACTIVE"
        # Not admitted -- Phase C must not fabricate a billing-readiness
        # evaluation for a referral/non-admitted record.
        assert payload["impact"]["billing_readiness_reevaluated"] is False
        assert payload["impact"]["admission_gate_status"] == "CLEAR"

        history = client.get(
            f"/billing/readiness-history/{patient.id}",
            headers=_headers("BILLING", tenant.id),
            params={"tenant_id": str(tenant.id)},
        )
        assert history.status_code == 200, history.text
        audit_events = [e for e in history.json()["audit_trail"] if e["entity_type"] == "ELIGIBILITY_VERIFICATION"]
        assert len(audit_events) == 1
        assert audit_events[0]["event_type"] == "CREATED"

    def test_second_verification_is_reverified_and_supersedes_prior(self, db_session, client):
        tenant = _billing_tenant(db_session)
        patient = _make_patient(db_session, str(tenant.id), mrn="MRN-VERIFY-2")
        source_doc = self._make_source_document(db_session, tenant, patient)

        record_eligibility_verification(
            db_session,
            tenant_id=str(tenant.id),
            patient_id=str(patient.id),
            source_document_id=str(source_doc.id),
            verified_by_user_id=str(uuid.UUID("11111111-1111-1111-1111-111111111111")),
            status="PENDING",
        )

        response = client.post(
            f"/billing/eligibility/{patient.id}/verifications",
            headers=_headers("BILLING", tenant.id),
            json={
                "tenant_id": str(tenant.id),
                "source_document_id": str(source_doc.id),
                "status": "VERIFIED_ACTIVE",
                "payer_change_flag": True,
                "notes": "Payer changed on reverification",
            },
        )
        assert response.status_code == 200, response.text

        history = client.get(
            f"/billing/readiness-history/{patient.id}",
            headers=_headers("BILLING", tenant.id),
            params={"tenant_id": str(tenant.id)},
        )
        audit_events = [
            e for e in history.json()["audit_trail"] if e["entity_type"] == "ELIGIBILITY_VERIFICATION"
        ]
        # Newest-first: the reverification event is first.
        assert audit_events[0]["event_type"] == "REVERIFIED"
        assert audit_events[0]["new_value"]["payer_change_flag"] is True

    def test_billing_readiness_reevaluated_for_admitted_patient(self, db_session, client):
        tenant = _billing_tenant(db_session)
        patient = _ready_admitted_patient(db_session, tenant.id, mrn="MRN-VERIFY-3")
        source_doc = self._make_source_document(db_session, tenant, patient)

        verdict_count_before = (
            db_session.query(BillingReadinessVerdict)
            .filter(BillingReadinessVerdict.patient_id == patient.id)
            .count()
        )

        response = client.post(
            f"/billing/eligibility/{patient.id}/verifications",
            headers=_headers("BILLING", tenant.id),
            json={
                "tenant_id": str(tenant.id),
                "source_document_id": str(source_doc.id),
                "status": "VERIFIED_ACTIVE",
            },
        )
        assert response.status_code == 200, response.text
        impact = response.json()["impact"]
        assert impact["billing_readiness_reevaluated"] is True
        # Phase 6 gating: readiness also requires a CONFIRMED benefit-period
        # determination, which this patient doesn't have yet -- so
        # NOT_READY (with a blocker) is the *correct* outcome here, proving
        # the reverification genuinely re-ran readiness rather than just
        # recording a verdict blindly.
        assert impact["readiness_status"] == "NOT_READY"
        assert impact["blockers"]

        verdict_count_after = (
            db_session.query(BillingReadinessVerdict)
            .filter(BillingReadinessVerdict.patient_id == patient.id)
            .count()
        )
        assert verdict_count_after == verdict_count_before + 1


class TestPhaseDRnReviewActions:
    def test_reason_is_required(self, db_session, client):
        tenant = _billing_tenant(db_session)
        patient = _make_patient(db_session, str(tenant.id), mrn="MRN-RN-1")

        response = client.post(
            f"/billing/eligibility/{patient.id}/rn-review-actions",
            headers=_headers("BILLING", tenant.id),
            json={"tenant_id": str(tenant.id), "action": "APPROVE_DETERMINATION", "reason": ""},
        )
        assert response.status_code == 400

    def test_approve_determination_clears_admission_gate(self, db_session, client):
        tenant = _billing_tenant(db_session)
        patient = _make_patient(db_session, str(tenant.id), mrn="MRN-RN-2")

        response = client.post(
            f"/billing/eligibility/{patient.id}/rn-review-actions",
            headers=_headers("BILLING", tenant.id),
            json={
                "tenant_id": str(tenant.id),
                "action": "APPROVE_DETERMINATION",
                "reason": "RN reviewed and confirmed benefit period 1",
                "anticipated_benefit_period_number": 1,
            },
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["determination_status"] == "BENEFIT_PERIOD_CONFIRMED"
        assert payload["anticipated_benefit_period_number"] == 1
        assert payload["impact"]["admission_gate_status"] == "CLEAR"

    def test_place_then_release_admission_hold(self, db_session, client):
        tenant = _billing_tenant(db_session)
        patient = _make_patient(db_session, str(tenant.id), mrn="MRN-RN-3")

        hold = client.post(
            f"/billing/eligibility/{patient.id}/rn-review-actions",
            headers=_headers("BILLING", tenant.id),
            json={
                "tenant_id": str(tenant.id),
                "action": "PLACE_ADMISSION_HOLD",
                "reason": "Coverage conflict discovered, holding admission",
            },
        )
        assert hold.status_code == 200, hold.text
        assert hold.json()["impact"]["admission_gate_status"] == "ADMISSION_REVIEW_REQUIRED"

        release = client.post(
            f"/billing/eligibility/{patient.id}/rn-review-actions",
            headers=_headers("BILLING", tenant.id),
            json={
                "tenant_id": str(tenant.id),
                "action": "RELEASE_ADMISSION_HOLD",
                "reason": "Conflict resolved, releasing hold",
            },
        )
        assert release.status_code == 200, release.text
        assert release.json()["impact"]["admission_gate_status"] == "CLEAR"

    def test_mark_f2f_required_toggles_flag_only(self, db_session, client):
        tenant = _billing_tenant(db_session)
        patient = _make_patient(db_session, str(tenant.id), mrn="MRN-RN-4")

        response = client.post(
            f"/billing/eligibility/{patient.id}/rn-review-actions",
            headers=_headers("BILLING", tenant.id),
            json={
                "tenant_id": str(tenant.id),
                "action": "MARK_F2F_REQUIRED",
                "reason": "Third benefit period, F2F applies",
            },
        )
        assert response.status_code == 200, response.text
        assert response.json()["determination_status"] == "REVIEW_IN_PROGRESS"

    def test_unknown_action_rejected(self, db_session, client):
        tenant = _billing_tenant(db_session)
        patient = _make_patient(db_session, str(tenant.id), mrn="MRN-RN-5")

        response = client.post(
            f"/billing/eligibility/{patient.id}/rn-review-actions",
            headers=_headers("BILLING", tenant.id),
            json={"tenant_id": str(tenant.id), "action": "DO_SOMETHING_ELSE", "reason": "x"},
        )
        assert response.status_code == 400


class TestPhaseEBillerActions:
    def test_escalate_creates_follow_up_and_audit_event(self, db_session, client):
        tenant = _billing_tenant(db_session)
        patient = _make_patient(db_session, str(tenant.id), mrn="MRN-BILLER-1")

        response = client.post(
            f"/billing/eligibility/{patient.id}/escalate",
            headers=_headers("BILLING", tenant.id),
            json={
                "tenant_id": str(tenant.id),
                "issue_type": "msp",
                "notes": "MSP questionnaire conflicts with payer response",
            },
        )
        assert response.status_code == 200, response.text
        assert response.json()["event_type"] == "ESCALATED_MSP"

        follow_up = (
            db_session.query(ReadinessFollowUp)
            .filter(ReadinessFollowUp.patient_id == patient.id)
            .one()
        )
        assert follow_up.follow_up_required is True
        assert follow_up.status == "OPEN"
        assert "ESCALATION[MSP]" in follow_up.notes

    def test_escalate_rejects_unknown_issue_type(self, db_session, client):
        tenant = _billing_tenant(db_session)
        patient = _make_patient(db_session, str(tenant.id), mrn="MRN-BILLER-2")

        response = client.post(
            f"/billing/eligibility/{patient.id}/escalate",
            headers=_headers("BILLING", tenant.id),
            json={"tenant_id": str(tenant.id), "issue_type": "WEATHER", "notes": "n/a"},
        )
        assert response.status_code == 400

    def test_document_review_request_404_for_unknown_document(self, db_session, client):
        tenant = _billing_tenant(db_session)
        patient = _make_patient(db_session, str(tenant.id), mrn="MRN-BILLER-3")

        response = client.post(
            f"/billing/eligibility/{patient.id}/document-review-requests",
            headers=_headers("BILLING", tenant.id),
            json={"tenant_id": str(tenant.id), "source_document_id": str(uuid.uuid4())},
        )
        assert response.status_code == 404

    def test_add_note_rejects_empty_note(self, db_session, client):
        tenant = _billing_tenant(db_session)
        patient = _make_patient(db_session, str(tenant.id), mrn="MRN-BILLER-4")

        response = client.post(
            f"/billing/eligibility/{patient.id}/notes",
            headers=_headers("BILLING", tenant.id),
            json={"tenant_id": str(tenant.id), "note": "   "},
        )
        assert response.status_code == 400

    def test_add_note_success_and_visible_in_audit_trail(self, db_session, client):
        tenant = _billing_tenant(db_session)
        patient = _make_patient(db_session, str(tenant.id), mrn="MRN-BILLER-5")

        response = client.post(
            f"/billing/eligibility/{patient.id}/notes",
            headers=_headers("BILLING", tenant.id),
            json={"tenant_id": str(tenant.id), "note": "Called payer, awaiting callback."},
        )
        assert response.status_code == 200, response.text

        history = client.get(
            f"/billing/readiness-history/{patient.id}",
            headers=_headers("BILLING", tenant.id),
            params={"tenant_id": str(tenant.id)},
        )
        assert history.status_code == 200, history.text
        note_events = [e for e in history.json()["audit_trail"] if e["entity_type"] == "BILLER_NOTE"]
        assert len(note_events) == 1
        assert note_events[0]["new_value"]["note"] == "Called payer, awaiting callback."
