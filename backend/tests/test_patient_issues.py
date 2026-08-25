from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.core.security import create_access_token
from app.models.patient import Patient
from app.models.patient_issue import PatientIssue
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


def _make_patient(db_session, tenant_id: uuid.UUID, *, mrn_prefix: str = "ISSUE") -> Patient:
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"{mrn_prefix}-{uuid.uuid4().hex[:10]}",
        date_of_birth=date(1945, 5, 5),
        primary_diagnosis="Hospice patient issue tracking diagnosis",
        status="ACTIVE",
        admission_status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


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
                full_name="Patient Issue Test User",
                role=role,
                active=True,
            )
        )
        db_session.commit()


@pytest.mark.integration
class TestPatientIssuesApi:
    def test_create_issue(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)

        response = client.post(
            "/patient-issues",
            headers=_headers(TEST_USER_ID, "RN", tenant_id),
            json={
                "patient_id": str(patient.id),
                "category": "clinical",
                "description": "Breakthrough pain requiring medication review.",
                "identified_date": "2026-08-24",
            },
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["patient_id"] == str(patient.id)
        assert body["category"] == "clinical"
        assert body["status"] == "OPEN"
        assert body["identified_by"] == str(TEST_USER_ID)

        stored = db_session.get(PatientIssue, uuid.UUID(body["id"]))
        assert stored is not None
        assert stored.description == "Breakthrough pain requiring medication review."
        assert stored.status == "OPEN"

    def test_list_issues_for_patient(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        other_patient = _make_patient(db_session, tenant_id, mrn_prefix="OTHER")
        db_session.add_all(
            [
                PatientIssue(
                    tenant_id=tenant_id,
                    patient_id=patient.id,
                    category="caregiver",
                    description="Family caregiver fatigued overnight.",
                    identified_date=date(2026, 8, 23),
                    identified_by=TEST_USER_ID,
                    status="RESOLVED",
                    outcome_notes="Weekend respite arranged.",
                    resolved_date=date(2026, 8, 24),
                    resolved_by=TEST_USER_ID,
                ),
                PatientIssue(
                    tenant_id=tenant_id,
                    patient_id=patient.id,
                    category="clinical",
                    description="Shortness of breath increased with exertion.",
                    identified_date=date(2026, 8, 24),
                    identified_by=TEST_USER_ID,
                    status="OPEN",
                ),
                PatientIssue(
                    tenant_id=tenant_id,
                    patient_id=other_patient.id,
                    category="safety",
                    description="Fall hazard unrelated patient.",
                    identified_date=date(2026, 8, 25),
                    identified_by=TEST_USER_ID,
                    status="OPEN",
                ),
            ]
        )
        db_session.commit()

        response = client.get(
            f"/patient-issues/patient/{patient.id}",
            headers=_headers(TEST_USER_ID, "RN", tenant_id),
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert [item["description"] for item in body] == [
            "Shortness of breath increased with exertion.",
            "Family caregiver fatigued overnight.",
        ]

        filtered = client.get(
            f"/patient-issues/patient/{patient.id}",
            headers=_headers(TEST_USER_ID, "RN", tenant_id),
            params={"status": "resolved"},
        )
        assert filtered.status_code == 200, filtered.text
        filtered_body = filtered.json()
        assert len(filtered_body) == 1
        assert filtered_body[0]["status"] == "RESOLVED"

    def test_update_and_resolve_issue(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        issue = PatientIssue(
            tenant_id=tenant_id,
            patient_id=patient.id,
            category="psychosocial",
            description="Patient expressing anticipatory grief.",
            identified_date=date(2026, 8, 20),
            identified_by=TEST_USER_ID,
            status="OPEN",
        )
        db_session.add(issue)
        db_session.commit()

        response = client.patch(
            f"/patient-issues/{issue.id}",
            headers=_headers(TEST_USER_ID, "MSW", tenant_id),
            json={
                "status": "RESOLVED",
                "outcome_notes": "MSW counseling visit completed and follow-up scheduled.",
                "resolved_date": "2026-08-25",
            },
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["status"] == "RESOLVED"
        assert body["outcome_notes"] == "MSW counseling visit completed and follow-up scheduled."
        assert body["resolved_date"] == "2026-08-25"
        assert body["resolved_by"] == str(TEST_USER_ID)

        db_session.refresh(issue)
        assert issue.status == "RESOLVED"
        assert issue.resolved_date == date(2026, 8, 25)
        assert issue.resolved_by == TEST_USER_ID

    def test_cross_tenant_access_is_rejected(self, client, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        issue = PatientIssue(
            tenant_id=tenant_id,
            patient_id=patient.id,
            category="safety",
            description="Oxygen tubing creates hallway trip hazard.",
            identified_date=date(2026, 8, 24),
            identified_by=TEST_USER_ID,
            status="OPEN",
        )
        db_session.add(issue)
        db_session.commit()

        other_tenant_id = uuid.uuid4()
        other_user_id = uuid.uuid4()
        _ensure_tenant_and_user(db_session, other_tenant_id, other_user_id)

        list_response = client.get(
            f"/patient-issues/patient/{patient.id}",
            headers=_headers(other_user_id, "RN", other_tenant_id),
        )
        assert list_response.status_code == 404, list_response.text

        update_response = client.patch(
            f"/patient-issues/{issue.id}",
            headers=_headers(other_user_id, "RN", other_tenant_id),
            json={"status": "RESOLVED", "outcome_notes": "Should never succeed."},
        )
        assert update_response.status_code == 404, update_response.text
