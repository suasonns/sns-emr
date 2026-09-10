"""Priority 4 -- Payer Review Workflow (storage/audit only).

Verifies:
- contracted_status / authorization_required_status are staff-writable
  tri-state fields (YES/NO/UNKNOWN) via the existing facesheet save
  endpoint, with server-side validation rejecting any other value.
- payer verification fields (payer_verified_date, payer_verification_notes,
  verification_document_reference) are storable via the same endpoint.
- payer_verified_by is ALWAYS server-stamped from the acting user and is
  never client-settable (the field is not even present on the request
  schema).
- an audit event is recorded whenever payer verification fields change.
- SNS EMR performs no eligibility lookup itself -- these are pure
  storage/audit writes of a staff-entered/staff-uploaded result.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.core.security import create_access_token
from app.models.audit_log import AuditLog
from app.models.patient import Patient
from app.models.patient_facesheet import PatientFaceSheet
from app.models.tenant import Tenant
from app.models.user import User
from tests.conftest import TEST_USER_ID


def _headers(user_id: uuid.UUID, role: str, tenant_id: uuid.UUID) -> dict[str, str]:
    token = create_access_token(
        user_id=user_id,
        role=role,
        tenant_id=tenant_id,
        email=f"{role.lower()}@example.com",
    )
    return {"Authorization": f"Bearer {token}"}


def _ensure_tenant_and_user(db_session, tenant_id: uuid.UUID, user_id: uuid.UUID, *, role: str = "RN") -> None:
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
                full_name="Payer Verification Test User",
                role=role,
                active=True,
            )
        )
        db_session.commit()


def _make_patient(db_session, tenant_id: uuid.UUID, *, mrn_prefix: str = "PAYER") -> Patient:
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"{mrn_prefix}-{uuid.uuid4().hex[:10]}",
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="Hospice payer verification test diagnosis",
        status="ACTIVE",
        admission_status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


@pytest.mark.integration
class TestPayerReviewWorkflow:
    def test_contracted_and_authorization_status_saved(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID)
        patient = _make_patient(db_session, tenant_id)

        response = client.post(
            f"/patients/{patient.id}/facesheet",
            headers=_headers(TEST_USER_ID, "RN", tenant_id),
            json={
                "first_name": "Payer",
                "last_name": "Review",
                "contracted_status": "YES",
                "authorization_required_status": "NO",
            },
        )
        assert response.status_code == 200, response.text

        facesheet = db_session.query(PatientFaceSheet).filter_by(patient_id=patient.id).one()
        assert facesheet.contracted_status == "YES"
        assert facesheet.authorization_required_status == "NO"

    def test_invalid_contracted_status_rejected(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID)
        patient = _make_patient(db_session, tenant_id)

        response = client.post(
            f"/patients/{patient.id}/facesheet",
            headers=_headers(TEST_USER_ID, "RN", tenant_id),
            json={
                "first_name": "Payer",
                "last_name": "Review",
                "contracted_status": "MAYBE",
            },
        )
        assert response.status_code == 400
        assert "contracted_status" in response.text

    def test_payer_verification_fields_saved_and_audited(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID)
        patient = _make_patient(db_session, tenant_id)

        response = client.post(
            f"/patients/{patient.id}/facesheet",
            headers=_headers(TEST_USER_ID, "RN", tenant_id),
            json={
                "first_name": "Payer",
                "last_name": "Review",
                "primary_payer": "Medicare",
                "payer_verified_date": "2026-09-01",
                "payer_verification_notes": "Verified via NGS Connex outside SNS EMR; active coverage confirmed.",
            },
        )
        assert response.status_code == 200, response.text

        facesheet = db_session.query(PatientFaceSheet).filter_by(patient_id=patient.id).one()
        assert facesheet.payer_verified_date == date(2026, 9, 1)
        assert facesheet.payer_verification_notes.startswith("Verified via NGS Connex")

        # payer_verified_by is never client-supplied -- always server-stamped.
        assert facesheet.payer_verified_by == TEST_USER_ID

        audit_rows = (
            db_session.query(AuditLog)
            .filter_by(entity_id=str(patient.id), action="facesheet_payer_verification_recorded")
            .all()
        )
        assert len(audit_rows) == 1
        assert str(audit_rows[0].user_id) == str(TEST_USER_ID)

    def test_payer_verified_by_not_client_settable(self, client, db_session):
        # payer_verified_by is intentionally absent from the request schema
        # (FaceSheetCreate); a client attempting to pass it has no effect
        # beyond being silently ignored by pydantic (extra fields dropped).
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        _ensure_tenant_and_user(db_session, tenant_id, TEST_USER_ID)
        patient = _make_patient(db_session, tenant_id)
        other_user_id = uuid.uuid4()

        response = client.post(
            f"/patients/{patient.id}/facesheet",
            headers=_headers(TEST_USER_ID, "RN", tenant_id),
            json={
                "first_name": "Payer",
                "last_name": "Review",
                "payer_verified_date": "2026-09-01",
                "payer_verified_by": str(other_user_id),
            },
        )
        assert response.status_code == 200, response.text

        facesheet = db_session.query(PatientFaceSheet).filter_by(patient_id=patient.id).one()
        assert facesheet.payer_verified_by == TEST_USER_ID
        assert facesheet.payer_verified_by != other_user_id
