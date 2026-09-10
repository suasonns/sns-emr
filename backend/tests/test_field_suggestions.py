from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest

from app.core.security import create_access_token
from app.models.audit_log import AuditLog
from app.models.facesheet_field_suggestion import FacesheetFieldSuggestion
from app.models.patient import Patient
from app.models.patient_facesheet import PatientFaceSheet
from app.models.tenant import Tenant
from app.models.user import User
from app.services.insurance_field_extraction import extract_insurance_candidates
from tests.conftest import TEST_USER_ID
from app.api.patients import persist_patient_from_hnp_extraction


def _headers(user_id: uuid.UUID, role: str, tenant_id: uuid.UUID) -> dict[str, str]:
    token = create_access_token(
        user_id=user_id,
        role=role,
        tenant_id=tenant_id,
        email=f"{role.lower()}@example.com",
    )
    return {"Authorization": f"Bearer {token}"}


def _ensure_tenant_and_user(db_session, tenant_id: uuid.UUID, user_id: uuid.UUID, *, role: str = "ADMINISTRATOR") -> None:
    if db_session.get(Tenant, tenant_id) is None:
        db_session.add(
            Tenant(
                id=tenant_id,
                legal_name=f"Tenant {tenant_id.hex[:8]}",
                display_name=f"Tenant {tenant_id.hex[:8]}",
                npi=f"{int(str(tenant_id.int)[:10]):010d}",
                tenant_type="DEV",
                status="ACTIVE",
            )
        )
        db_session.commit()
    if db_session.get(User, user_id) is None:
        db_session.add(
            User(
                id=user_id,
                tenant_id=tenant_id,
                email=f"user.{user_id.hex[:8]}@example.com",
                full_name="Field Suggestion Test User",
                role=role,
                active=True,
            )
        )
        db_session.commit()


def _make_patient_with_facesheet(db_session, tenant_id: uuid.UUID) -> tuple[Patient, PatientFaceSheet]:
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"FS-{uuid.uuid4().hex[:10]}",
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="Field suggestion test diagnosis",
        status="ACTIVE",
        admission_status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.flush()

    facesheet = PatientFaceSheet(
        tenant_id=tenant_id,
        patient_id=patient.id,
        first_name="Test",
        last_name="Patient",
        dob=date(1940, 1, 1),
        created_by=TEST_USER_ID,
        updated_by=TEST_USER_ID,
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(facesheet)
    db_session.commit()
    return patient, facesheet


class TestInsuranceFieldExtraction:
    def test_extracts_mbi_policy_and_payer(self):
        text = (
            "Patient insurance card on file. Medicare Beneficiary Identifier: 1EG4TE5MK73. "
            "Policy Number: ABC123456. Payer: Medicare."
        )
        candidates = extract_insurance_candidates(text)
        assert candidates.get("mbi_number") == "1EG4TE5MK73"
        assert candidates.get("primary_policy_number") == "ABC123456"
        assert candidates.get("primary_payer") == "Medicare"

    def test_returns_empty_for_unrelated_text(self):
        assert extract_insurance_candidates("Patient reports stable vital signs today.") == {}

    def test_returns_empty_for_empty_text(self):
        assert extract_insurance_candidates("") == {}
        assert extract_insurance_candidates(None) == {}


@pytest.mark.integration
class TestFieldSuggestionReviewApi:
    def test_list_defaults_to_actionable_statuses(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID)
        patient, _facesheet = _make_patient_with_facesheet(db_session, tenant_id)

        db_session.add_all(
            [
                FacesheetFieldSuggestion(
                    tenant_id=tenant_id,
                    patient_id=patient.id,
                    field_name="mbi_number",
                    current_value=None,
                    suggested_value="1EG4TE5MK73",
                    status="pending",
                    created_by=TEST_USER_ID,
                ),
                FacesheetFieldSuggestion(
                    tenant_id=tenant_id,
                    patient_id=patient.id,
                    field_name="primary_payer",
                    current_value="Aetna",
                    suggested_value="Medicare",
                    status="rejected",
                    created_by=TEST_USER_ID,
                ),
            ]
        )
        db_session.commit()

        response = client.get(
            f"/field-suggestions?patient_id={patient.id}",
            headers=_headers(TEST_USER_ID, "ADMINISTRATOR", tenant_id),
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert len(body) == 1
        assert body[0]["field_name"] == "mbi_number"
        assert body[0]["status"] == "pending"

    def test_accept_pending_suggestion_updates_facesheet_and_audits(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID)
        patient, facesheet = _make_patient_with_facesheet(db_session, tenant_id)
        assert facesheet.mbi_number is None

        suggestion = FacesheetFieldSuggestion(
            tenant_id=tenant_id,
            patient_id=patient.id,
            field_name="mbi_number",
            current_value=None,
            suggested_value="1EG4TE5MK73",
            status="pending",
            created_by=TEST_USER_ID,
        )
        db_session.add(suggestion)
        db_session.commit()
        suggestion_id = suggestion.id

        response = client.post(
            f"/field-suggestions/{suggestion_id}/accept",
            headers=_headers(TEST_USER_ID, "ADMINISTRATOR", tenant_id),
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["status"] == "accepted"

        db_session.expire_all()
        updated_facesheet = (
            db_session.query(PatientFaceSheet)
            .filter(PatientFaceSheet.patient_id == patient.id)
            .first()
        )
        assert updated_facesheet.mbi_number == "1EG4TE5MK73"

        updated_suggestion = db_session.get(FacesheetFieldSuggestion, suggestion_id)
        assert updated_suggestion.status == "accepted"
        assert updated_suggestion.resolved_at is not None

        audit_rows = (
            db_session.query(AuditLog)
            .filter(AuditLog.action == "facesheet_field_suggestion_accepted")
            .all()
        )
        assert len(audit_rows) == 1

    def test_reject_pending_suggestion_leaves_facesheet_untouched(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID)
        patient, facesheet = _make_patient_with_facesheet(db_session, tenant_id)

        suggestion = FacesheetFieldSuggestion(
            tenant_id=tenant_id,
            patient_id=patient.id,
            field_name="primary_payer",
            current_value=None,
            suggested_value="Aetna",
            status="pending",
            created_by=TEST_USER_ID,
        )
        db_session.add(suggestion)
        db_session.commit()
        suggestion_id = suggestion.id

        response = client.post(
            f"/field-suggestions/{suggestion_id}/reject",
            headers=_headers(TEST_USER_ID, "ADMINISTRATOR", tenant_id),
        )
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "rejected"

        db_session.expire_all()
        updated_facesheet = (
            db_session.query(PatientFaceSheet)
            .filter(PatientFaceSheet.patient_id == patient.id)
            .first()
        )
        assert updated_facesheet.primary_payer is None

    def test_dismiss_suggestion(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID)
        patient, _facesheet = _make_patient_with_facesheet(db_session, tenant_id)

        suggestion = FacesheetFieldSuggestion(
            tenant_id=tenant_id,
            patient_id=patient.id,
            field_name="primary_policy_number",
            current_value=None,
            suggested_value="XYZ999",
            status="pending",
            created_by=TEST_USER_ID,
        )
        db_session.add(suggestion)
        db_session.commit()
        suggestion_id = suggestion.id

        response = client.post(
            f"/field-suggestions/{suggestion_id}/dismiss",
            headers=_headers(TEST_USER_ID, "ADMINISTRATOR", tenant_id),
        )
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "dismissed"

    def test_accept_already_resolved_suggestion_conflicts(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID)
        patient, _facesheet = _make_patient_with_facesheet(db_session, tenant_id)

        suggestion = FacesheetFieldSuggestion(
            tenant_id=tenant_id,
            patient_id=patient.id,
            field_name="mbi_number",
            current_value=None,
            suggested_value="1EG4TE5MK73",
            status="rejected",
            created_by=TEST_USER_ID,
            resolved_at=datetime.now(timezone.utc),
            resolved_by=TEST_USER_ID,
        )
        db_session.add(suggestion)
        db_session.commit()
        suggestion_id = suggestion.id

        response = client.post(
            f"/field-suggestions/{suggestion_id}/accept",
            headers=_headers(TEST_USER_ID, "ADMINISTRATOR", tenant_id),
        )
        assert response.status_code == 409, response.text


@pytest.mark.integration
class TestHnpIngestionQueuesInsuranceCandidates:
    def test_new_patient_hnp_ingest_with_insurance_text_queues_suggestions(self, db_session):
        """End-to-end: OCR/extraction finds an MBI/policy/payer in raw
        document text -> a FacesheetFieldSuggestion is queued (never
        auto-written to PatientFaceSheet) -> staff must accept it via the
        review API before it becomes authoritative. Demonstrates the full
        chain required by the Priority 3 validation."""
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID)

        raw_text = (
            "Name: Insurance Candidate\n"
            "MRN: FS-HNP-001\n"
            "Date of birth: 02/02/1950\n"
            "Sex: Male\n"
            "Diagnosis: Chronic heart failure Noted on: 2026-01-05\n"
            "Insurance: Medicare Beneficiary Identifier 1EG4TE5MK73. "
            "Policy Number: ABC123456. Payer: Medicare.\n"
        )

        result = persist_patient_from_hnp_extraction(
            db_session,
            tenant_id=tenant_id,
            user_id=TEST_USER_ID,
            raw_text=raw_text,
            source_name="HNP",
        )
        patient_id = uuid.UUID(result["id"])

        facesheet = (
            db_session.query(PatientFaceSheet)
            .filter(PatientFaceSheet.patient_id == patient_id)
            .one()
        )
        # OCR never writes insurance fields directly, even for a brand new
        # facesheet with no prior value.
        assert facesheet.mbi_number is None
        assert facesheet.primary_payer is None
        assert facesheet.primary_policy_number is None

        suggestions = {
            row.field_name: row
            for row in db_session.query(FacesheetFieldSuggestion)
            .filter(FacesheetFieldSuggestion.patient_id == patient_id)
            .all()
        }
        assert suggestions["mbi_number"].suggested_value == "1EG4TE5MK73"
        assert suggestions["mbi_number"].status == "pending"
        assert suggestions["primary_policy_number"].suggested_value == "ABC123456"
        assert suggestions["primary_payer"].suggested_value == "Medicare"

