from __future__ import annotations

import pytest
from sqlalchemy import text

from app.models.patient import Patient


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

    patient = db_session.query(Patient).first()
    if not patient:
        pytest.skip("No patient found in DB. Seed a patient before running integration tests.")

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