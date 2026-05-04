import pytest
from sqlalchemy import text

from app.models.audit_log import AuditLog
from app.models.patient import Patient


@pytest.mark.integration
def test_audit_log_written_on_create_visit(client, rn_headers, db_session):
    # --- Debug: prove which DB/schema pytest is using ---
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
    print("HAS visits.chha_poc_id:", has_col)

    # Skip cleanly if schema is not migrated
    if has_col == 0:
        pytest.skip(
            "Schema missing visits.chha_poc_id in this DB. "
            "Run: alembic upgrade head against the DATABASE_URL used by tests."
        )

    # --- Actual test logic ---
    patient = db_session.query(Patient).first()
    if not patient:
        pytest.skip(
            "No patient found in DB. Seed a patient before running integration tests."
        )

    response = client.post(
        "/visits/",
        headers=rn_headers,
        params={
            "patient_id": str(patient.id),
            "visit_type": "RN",
        },
    )
    assert response.status_code == 201, response.text
    visit_id = response.json()["visit_id"]

    row = (
        db_session.query(AuditLog)
        .filter(AuditLog.action == "CREATE_VISIT")
        .filter(AuditLog.entity_type == "visit")
        .filter(AuditLog.entity_id == str(visit_id))
        .order_by(AuditLog.created_at.desc())
        .first()
    )

    assert row is not None, "Expected audit log row for CREATE_VISIT"