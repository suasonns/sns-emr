from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import text

from app.models.admission import Admission
from app.models.patient import Patient
from tests.conftest import TEST_USER_ID, _test_tenant_id


@pytest.mark.integration
def test_audit_log_written_on_create_visit(client, rn_headers, db_session):
    # --- Verify DB context ---
    db_name = db_session.execute(text("SELECT current_database()")).scalar()
    schema = db_session.execute(text("SELECT current_schema()")).scalar()
    print("TEST DB:", db_name, "SCHEMA:", schema)

    has_col = db_session.execute(
        text(
            """
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_name = 'visits'
              AND column_name = 'chha_poc_id'
            """
        )
    ).scalar()

    if has_col == 0:
        pytest.skip(
            "Schema missing visits.chha_poc_id. "
            "Run alembic upgrade head against the test DATABASE_URL."
        )

    # Scope to the active test tenant, creating a patient if none exists yet.
    # An unscoped .first() previously picked up whatever Patient row happened
    # to sort first across all tenants in the shared dev DB, which is
    # data/order-dependent and can return a patient outside rn_headers'
    # tenant (404 Patient not found). Tests must only see/create rows in
    # their own designated testing tenant.
    tenant_id = uuid.UUID(_test_tenant_id())
    patient = (
        db_session.query(Patient)
        .filter(Patient.tenant_id == tenant_id)
        .first()
    )
    if not patient:
        patient = Patient(
            tenant_id=tenant_id,
            mrn=f"AUDIT-{uuid.uuid4().hex[:8]}",
            date_of_birth=date(1940, 1, 1),
            primary_diagnosis="C34.90",
            status="ACTIVE",
            admission_status="PRE_REFERRAL",
            created_by=TEST_USER_ID,
        )
        db_session.add(patient)
        db_session.commit()

    # An SOC visit requires a resolvable ADMITTED admission (see
    # app/api/visits.py:_create_visit "active admitted admission" check).
    # Ensure one exists for this tenant/patient before posting the visit.
    admitted = (
        db_session.query(Admission)
        .filter(
            Admission.patient_id == patient.id,
            Admission.tenant_id == tenant_id,
            Admission.status == "ADMITTED",
        )
        .first()
    )
    if not admitted:
        admitted = Admission(
            tenant_id=tenant_id,
            patient_id=patient.id,
            admission_date=datetime.now(timezone.utc),
            status="ADMITTED",
            created_by=TEST_USER_ID,
        )
        db_session.add(admitted)
        db_session.commit()

    # form_registry is a global (non-tenant-scoped) configuration table that
    # the visit form resolver depends on (app/domain/forms/form_resolution_
    # service.py). It is not touched by the tenant-scoped cleanup in
    # conftest.py, so its emptiness here is a pre-existing environment/seed
    # data gap, not a test-isolation defect. Skip rather than mask it.
    has_active_rn_routine_form = db_session.execute(
        text(
            "SELECT 1 FROM form_registry "
            "WHERE form_key = 'RN_ROUTINE' AND is_active = TRUE LIMIT 1"
        )
    ).first()
    if not has_active_rn_routine_form:
        pytest.skip(
            "form_registry has no active RN_ROUTINE form configured in this "
            "environment. Seed form_registry (global config, not tenant-"
            "scoped) before running this integration test."
        )

    response = client.post(
        "/visits/",
        headers=rn_headers,
        json={
            "patient_id": str(patient.id),
            "visit_type": "RN",
            "form_type": "ROUTINE_VISIT",
        },
    )
    assert response.status_code == 201, response.text
    visit_id = response.json()["visit_id"]

    row = db_session.execute(
        text(
            """
            SELECT id
            FROM audit_logs
            WHERE action = :action
              AND entity_type = :entity_type
              AND entity_id = :entity_id
            ORDER BY created_at DESC
            LIMIT 1
            """
        ),
        {
            "action": "CREATE_VISIT",
            "entity_type": "visit",
            "entity_id": str(visit_id),
        },
    ).first()

    assert row is not None, "Expected audit log row for CREATE_VISIT"