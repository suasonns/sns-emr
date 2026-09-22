"""
AC-003 remediation tests: app/api/adr_exports.py::export_adr

Prior behavior: export_adr had no authentication or authorization
dependency at all, and no tenant filter -- any caller (authenticated or
not) could export any patient's ADR/TPE packet.

Corrected behavior:
  - authentication + VIEW_ALL_TENANT_PATIENTS capability required (the
    same capability already required for Survey Mode compliance/export
    actions -- see AC-001), via app.core.capabilities.require_capability.
  - the client-supplied patient_id is bound to the authenticated user's
    own tenant via the existing app.core.patient_access.get_authorized_
    patient() helper (the same mechanism already used by
    app/api/patient_charts.py), instead of trusted as-is.
  - a successful export is now recorded via the existing audit
    infrastructure (app.services.audit_logger.log_event).
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.models.patient import Patient
from app.models.tenant import Tenant
from app.models.audit_log import AuditLog
from tests.conftest import TEST_USER_ID, _test_tenant_id, login_headers


def _make_patient(db_session, tenant_id=None):
    patient = Patient(
        tenant_id=tenant_id or uuid.UUID(_test_tenant_id()),
        mrn=f"ADR-{uuid.uuid4().hex[:8]}",
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="C34.90",
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.flush()
    db_session.commit()
    return patient


def _body(patient_id) -> dict:
    return {
        "patient_id": str(patient_id),
        "adr_start": "2026-06-01",
        "adr_end": "2026-06-30",
        "adr_mode": True,
        "mode": "ADR",
    }


def test_export_adr_requires_authentication(client, db_session):
    patient = _make_patient(db_session)
    response = client.post("/chart/export/adr", json=_body(patient.id))
    assert response.status_code == 401


def test_export_adr_denies_role_without_capability(client, db_session):
    patient = _make_patient(db_session)
    headers = login_headers(client, user_id="rn_test", role="RN")
    response = client.post("/chart/export/adr", json=_body(patient.id), headers=headers)
    assert response.status_code == 403


def test_export_adr_succeeds_for_authorized_same_tenant_request(client, db_session):
    patient = _make_patient(db_session)
    headers = login_headers(client, user_id="admin_test", role="ADMINISTRATOR")
    response = client.post("/chart/export/adr", json=_body(patient.id), headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


def test_export_adr_denies_cross_tenant_patient(client, db_session):
    other_tenant_id = uuid.uuid4()
    if db_session.get(Tenant, other_tenant_id) is None:
        db_session.add(
            Tenant(
                id=other_tenant_id,
                legal_name="Other Agency",
                display_name="Other Agency",
                npi="9999999990",
                tenant_type="DEV",
                status="ACTIVE",
            )
        )
        db_session.commit()

    patient = _make_patient(db_session, tenant_id=other_tenant_id)

    headers = login_headers(client, user_id="admin_test", role="ADMINISTRATOR")
    response = client.post("/chart/export/adr", json=_body(patient.id), headers=headers)
    assert response.status_code == 404


def test_export_adr_handles_nonexistent_patient(client, db_session):
    headers = login_headers(client, user_id="admin_test", role="ADMINISTRATOR")
    response = client.post("/chart/export/adr", json=_body(uuid.uuid4()), headers=headers)
    assert response.status_code == 404


def test_export_adr_handles_malformed_patient_id(client, db_session):
    headers = login_headers(client, user_id="admin_test", role="ADMINISTRATOR")
    body = _body("not-a-uuid")
    response = client.post("/chart/export/adr", json=body, headers=headers)
    assert response.status_code == 404


def test_export_adr_records_audit_event(client, db_session):
    patient = _make_patient(db_session)
    headers = login_headers(client, user_id="admin_test", role="ADMINISTRATOR")
    response = client.post("/chart/export/adr", json=_body(patient.id), headers=headers)
    assert response.status_code == 200

    event = (
        db_session.query(AuditLog)
        .filter(AuditLog.entity_id == str(patient.id), AuditLog.action == "ADR_EXPORT")
        .first()
    )
    assert event is not None
    assert event.role == "ADMINISTRATOR"
