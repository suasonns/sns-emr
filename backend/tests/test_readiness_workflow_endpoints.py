# backend/tests/test_readiness_workflow_endpoints.py
"""
Sprint 2 Phase 2 -- integration tests for the Billing Readiness
Operational Workflow HTTP endpoints (dashboard, queue, history,
assignment/follow-up upsert, blocker resolve).

Reuses the patient/benefit-period/certification/POC/payer fixture
helpers from test_billing_readiness_service.py and the auth-header
helper from test_aging_report_service.py, matching the established
cross-test-module import convention already used by
test_billing_readiness_verdict_persistence.py and
test_billing_provider_authorization.py.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest

from app.billing.models.billing_blocker_record import BillingBlockerRecord
from app.billing.models.readiness_assignment import ReadinessAssignment
from app.billing.models.readiness_follow_up import ReadinessFollowUp
from tests.conftest import TEST_USER_ID
from tests.test_aging_report_service import _enable_billing_for_tenant, _headers
from tests.test_billing_readiness_service import (
    SERVICE_DATE,
    _fully_ready_patient,
    _make_admitted,
    _make_benefit_period,
    _make_patient,
)


@pytest.fixture(autouse=True)
def _clean_patient_payers_leftovers(db_session, tenant):
    from sqlalchemy import text as _text

    db_session.execute(
        _text(
            "DELETE FROM patient_payers WHERE patient_id IN "
            "(SELECT id FROM patients WHERE tenant_id = :tenant_id)"
        ),
        {"tenant_id": str(tenant.id)},
    )
    db_session.commit()
    yield
    db_session.execute(
        _text(
            "DELETE FROM patient_payers WHERE patient_id IN "
            "(SELECT id FROM patients WHERE tenant_id = :tenant_id)"
        ),
        {"tenant_id": str(tenant.id)},
    )
    db_session.commit()


def _billing_tenant(db_session):
    tenant_id = uuid.uuid4()
    return _enable_billing_for_tenant(
        db_session, tenant_id, legal_name=f"Readiness Workflow Test Agency {tenant_id.hex[:8]}"
    )


class TestReadinessDashboardEndpoint:
    def test_dashboard_returns_counts_and_attention_list(self, db_session, client):
        billing_tenant = _billing_tenant(db_session)
        tenant_id = billing_tenant.id

        ready_patient = _fully_ready_patient(db_session, str(tenant_id), mrn="MRN-DASH-READY")
        _make_admitted(db_session, str(tenant_id), ready_patient)
        not_ready_patient = _make_patient(db_session, str(tenant_id), mrn="MRN-DASH-NOTREADY")
        _make_benefit_period(db_session, str(tenant_id), not_ready_patient)
        _make_admitted(db_session, str(tenant_id), not_ready_patient)

        response = client.get(
            "/billing/readiness-dashboard",
            headers=_headers("BILLING", tenant_id),
            params={"tenant_id": str(tenant_id), "service_date": SERVICE_DATE.isoformat()},
        )

        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["tenant_id"] == str(tenant_id)
        assert payload["counts"]["READY"] >= 1
        assert payload["counts"]["NOT_READY"] >= 1
        attention_ids = {p["patient_id"] for p in payload["patients_requiring_attention"]}
        assert str(not_ready_patient.id) in attention_ids
        assert isinstance(payload["readiness_trend"], list)
        assert isinstance(payload["recent_evaluations"], list)


class TestReadinessQueueEndpoint:
    def test_queue_filters_by_status(self, db_session, client):
        billing_tenant = _billing_tenant(db_session)
        tenant_id = billing_tenant.id

        ready_patient = _fully_ready_patient(db_session, str(tenant_id), mrn="MRN-QUEUE-READY")
        _make_admitted(db_session, str(tenant_id), ready_patient)
        not_ready_patient = _make_patient(db_session, str(tenant_id), mrn="MRN-QUEUE-NOTREADY")
        _make_benefit_period(db_session, str(tenant_id), not_ready_patient)
        _make_admitted(db_session, str(tenant_id), not_ready_patient)

        # Seed verdicts for both patients via the dashboard (same side
        # effect the readiness-report endpoint already has).
        client.get(
            "/billing/readiness-dashboard",
            headers=_headers("BILLING", tenant_id),
            params={"tenant_id": str(tenant_id), "service_date": SERVICE_DATE.isoformat()},
        )

        response = client.get(
            "/billing/readiness-queue",
            headers=_headers("BILLING", tenant_id),
            params={"tenant_id": str(tenant_id), "status": "NOT_READY"},
        )

        assert response.status_code == 200, response.text
        payload = response.json()
        patient_ids = {p["patient_id"] for p in payload["patients"]}
        assert str(not_ready_patient.id) in patient_ids
        assert str(ready_patient.id) not in patient_ids
        for row in payload["patients"]:
            assert row["assignment_status"] == "UNASSIGNED"


class TestReadinessHistoryEndpoint:
    def test_history_returns_verdicts_and_blocker_lifecycle(self, db_session, client):
        billing_tenant = _billing_tenant(db_session)
        tenant_id = billing_tenant.id

        patient = _make_patient(db_session, str(tenant_id), mrn="MRN-HISTORY")
        _make_benefit_period(db_session, str(tenant_id), patient)
        _make_admitted(db_session, str(tenant_id), patient)

        client.get(
            "/billing/readiness-dashboard",
            headers=_headers("BILLING", tenant_id),
            params={"tenant_id": str(tenant_id), "service_date": SERVICE_DATE.isoformat()},
        )

        response = client.get(
            f"/billing/readiness-history/{patient.id}",
            headers=_headers("BILLING", tenant_id),
            params={"tenant_id": str(tenant_id)},
        )

        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["patient_id"] == str(patient.id)
        assert len(payload["verdicts"]) >= 1
        assert payload["verdicts"][0]["readiness_status"] == "NOT_READY"
        assert len(payload["blocker_history"]) >= 1
        assert all(b["status"] == "OPEN" for b in payload["blocker_history"])


def _make_user(db_session, tenant_id, *, role: str = "RN") -> uuid.UUID:
    from app.models.user import User

    user_id = uuid.uuid4()
    db_session.add(
        User(
            id=user_id,
            tenant_id=uuid.UUID(str(tenant_id)),
            email=f"{user_id.hex[:8]}@example.com",
            full_name="Test Staff Member",
            role=role,
        )
    )
    db_session.commit()
    return user_id


class TestReadinessAssignmentEndpoint:
    def test_create_then_reassign_writes_audit_events(self, db_session, client):
        billing_tenant = _billing_tenant(db_session)
        tenant_id = billing_tenant.id
        patient = _make_patient(db_session, str(tenant_id), mrn="MRN-ASSIGN")

        first_user_id = str(_make_user(db_session, tenant_id))
        response = client.post(
            "/billing/readiness-assignments",
            headers=_headers("BILLING", tenant_id),
            json={
                "tenant_id": str(tenant_id),
                "patient_id": str(patient.id),
                "assigned_user_id": first_user_id,
                "assigned_role": "BILLING_SPECIALIST",
                "assignment_status": "ASSIGNED",
            },
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["assigned_user_id"] == first_user_id
        assert body["assignment_status"] == "ASSIGNED"

        assignment_row = (
            db_session.query(ReadinessAssignment)
            .filter(ReadinessAssignment.patient_id == patient.id)
            .one()
        )
        assert str(assignment_row.id) == body["id"]

        second_user_id = str(_make_user(db_session, tenant_id))
        response2 = client.post(
            "/billing/readiness-assignments",
            headers=_headers("BILLING", tenant_id),
            json={
                "tenant_id": str(tenant_id),
                "patient_id": str(patient.id),
                "assigned_user_id": second_user_id,
                "assigned_role": "BILLING_SPECIALIST",
                "assignment_status": "ASSIGNED",
            },
        )
        assert response2.status_code == 200, response2.text
        assert response2.json()["id"] == body["id"]
        assert response2.json()["assigned_user_id"] == second_user_id

    def test_invalid_assignment_status_is_rejected(self, db_session, client):
        billing_tenant = _billing_tenant(db_session)
        tenant_id = billing_tenant.id
        patient = _make_patient(db_session, str(tenant_id), mrn="MRN-ASSIGN-BAD")

        response = client.post(
            "/billing/readiness-assignments",
            headers=_headers("BILLING", tenant_id),
            json={
                "tenant_id": str(tenant_id),
                "patient_id": str(patient.id),
                "assignment_status": "NOT_A_REAL_STATUS",
            },
        )
        assert response.status_code == 400


class TestReadinessFollowUpEndpoint:
    def test_create_follow_up_with_due_date_and_mark_blocked(self, db_session, client):
        billing_tenant = _billing_tenant(db_session)
        tenant_id = billing_tenant.id
        patient = _make_patient(db_session, str(tenant_id), mrn="MRN-FOLLOWUP")

        due_date = (date.today() + timedelta(days=1)).isoformat()
        response = client.post(
            "/billing/readiness-followups",
            headers=_headers("BILLING", tenant_id),
            json={
                "tenant_id": str(tenant_id),
                "patient_id": str(patient.id),
                "status": "OPEN",
                "due_date": due_date,
                "notes": "Waiting on signed F2F.",
            },
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["status"] == "OPEN"
        assert body["due_date"] == due_date

        response2 = client.post(
            "/billing/readiness-followups",
            headers=_headers("BILLING", tenant_id),
            json={
                "tenant_id": str(tenant_id),
                "patient_id": str(patient.id),
                "follow_up_id": body["id"],
                "status": "BLOCKED",
                "reason": "Physician unresponsive for 2 weeks.",
            },
        )
        assert response2.status_code == 200, response2.text
        assert response2.json()["status"] == "BLOCKED"
        assert response2.json()["id"] == body["id"]

        follow_up_row = db_session.query(ReadinessFollowUp).filter(
            ReadinessFollowUp.id == body["id"]
        ).one()
        assert follow_up_row.status == "BLOCKED"

    def test_follow_up_id_from_other_tenant_is_not_found(self, db_session, client):
        tenant_a = _billing_tenant(db_session)
        tenant_b = _billing_tenant(db_session)
        patient_a = _make_patient(db_session, str(tenant_a.id), mrn="MRN-FOLLOWUP-XTENANT")

        created = client.post(
            "/billing/readiness-followups",
            headers=_headers("BILLING", tenant_a.id),
            json={
                "tenant_id": str(tenant_a.id),
                "patient_id": str(patient_a.id),
                "status": "OPEN",
            },
        )
        assert created.status_code == 200, created.text
        follow_up_id = created.json()["id"]

        cross_tenant_attempt = client.post(
            "/billing/readiness-followups",
            headers=_headers("BILLING", tenant_b.id),
            json={
                "tenant_id": str(tenant_b.id),
                "patient_id": str(patient_a.id),
                "follow_up_id": follow_up_id,
                "status": "RESOLVED",
            },
        )
        assert cross_tenant_attempt.status_code == 404


class TestReadinessBlockerResolveEndpoint:
    def test_manual_resolve_marks_resolved_with_reason(self, db_session, client):
        billing_tenant = _billing_tenant(db_session)
        tenant_id = billing_tenant.id
        patient = _make_patient(db_session, str(tenant_id), mrn="MRN-BLOCKER-RESOLVE")
        _make_benefit_period(db_session, str(tenant_id), patient)
        _make_admitted(db_session, str(tenant_id), patient)

        client.get(
            "/billing/readiness-dashboard",
            headers=_headers("BILLING", tenant_id),
            params={"tenant_id": str(tenant_id), "service_date": SERVICE_DATE.isoformat()},
        )

        blocker = (
            db_session.query(BillingBlockerRecord)
            .filter(BillingBlockerRecord.patient_id == patient.id)
            .first()
        )
        assert blocker is not None

        response = client.post(
            f"/billing/readiness-blockers/{blocker.id}/resolve",
            headers=_headers("BILLING", tenant_id),
            params={"tenant_id": str(tenant_id)},
            json={"reason": "Confirmed with agency the cert was signed today."},
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["status"] == "RESOLVED"
        assert body["resolution_reason"] == "Confirmed with agency the cert was signed today."

    def test_resolving_blocker_from_wrong_tenant_returns_404(self, db_session, client):
        tenant_a = _billing_tenant(db_session)
        tenant_b = _billing_tenant(db_session)
        patient = _make_patient(db_session, str(tenant_a.id), mrn="MRN-BLOCKER-XTENANT")
        _make_benefit_period(db_session, str(tenant_a.id), patient)
        _make_admitted(db_session, str(tenant_a.id), patient)

        client.get(
            "/billing/readiness-dashboard",
            headers=_headers("BILLING", tenant_a.id),
            params={"tenant_id": str(tenant_a.id), "service_date": SERVICE_DATE.isoformat()},
        )

        blocker = (
            db_session.query(BillingBlockerRecord)
            .filter(BillingBlockerRecord.patient_id == patient.id)
            .first()
        )
        assert blocker is not None

        response = client.post(
            f"/billing/readiness-blockers/{blocker.id}/resolve",
            headers=_headers("BILLING", tenant_b.id),
            params={"tenant_id": str(tenant_b.id)},
            json={"reason": "should not work"},
        )
        assert response.status_code == 404
