"""repair billing tables if missing

Revision ID: 4f7d7c237580
Revises: dd0d0d098c39
Create Date: 2026-05-30 16:18:31.184692
"""

from typing import Sequence, Union
from alembic import op


# revision identifiers
revision: str = "4f7d7c237580"
down_revision: Union[str, Sequence[str], None] = "dd0d0d098c39"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Repair migration:
    - Creates ALL billing tables if missing
    - Safe to run multiple times
    - fixes stamped-but-not-applied state
    """

    # ----------------------------
    # BILLING CORE TABLES
    # ----------------------------

    op.execute("""
    CREATE TABLE IF NOT EXISTS billing_cycles (
        id VARCHAR PRIMARY KEY,
        tenant_id VARCHAR NOT NULL,
        month INTEGER NOT NULL,
        year INTEGER NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL
    );
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS billing_summary (
        id VARCHAR PRIMARY KEY,
        patient_id VARCHAR NOT NULL,
        billing_cycle_id VARCHAR NOT NULL,
        total_units INTEGER NOT NULL,
        status VARCHAR NOT NULL,
        risk_score INTEGER NOT NULL
    );
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS billing_snapshot (
        id VARCHAR PRIMARY KEY,
        patient_id VARCHAR NOT NULL,
        data JSON NOT NULL
    );
    """)

    # ----------------------------
    # LOC + POS STRUCTURE
    # ----------------------------

    op.execute("""
    CREATE TABLE IF NOT EXISTS patient_pos (
        id VARCHAR PRIMARY KEY,
        patient_id VARCHAR NOT NULL,
        pos_type VARCHAR NOT NULL,
        facility_name VARCHAR,
        effective_date DATE NOT NULL,
        end_date DATE
    );
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS gip_periods (
        id VARCHAR PRIMARY KEY,
        patient_id VARCHAR NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        reason VARCHAR
    );
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS respite_periods (
        id VARCHAR PRIMARY KEY,
        patient_id VARCHAR NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        reason VARCHAR
    );
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS continuous_care_events (
        id VARCHAR PRIMARY KEY,
        patient_id VARCHAR NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        reason VARCHAR
    );
    """)

    # ----------------------------
    # VISITS + UNITS
    # ----------------------------

    op.execute("""
    CREATE TABLE IF NOT EXISTS visit_minutes (
        id VARCHAR PRIMARY KEY,
        visit_id VARCHAR NOT NULL,
        discipline VARCHAR NOT NULL,
        minutes INTEGER NOT NULL,
        units INTEGER NOT NULL
    );
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS orders_snapshot (
        id VARCHAR PRIMARY KEY,
        patient_id VARCHAR NOT NULL,
        discipline VARCHAR NOT NULL,
        visits_per_week INTEGER NOT NULL,
        effective_date DATE NOT NULL,
        end_date DATE
    );
    """)

    # ----------------------------
    # PAYER / AUTH / CONTRACT
    # ----------------------------

    op.execute("""
    CREATE TABLE IF NOT EXISTS patient_payers (
        id VARCHAR PRIMARY KEY,
        patient_id VARCHAR NOT NULL,
        payer_name VARCHAR NOT NULL,
        payer_type VARCHAR NOT NULL
    );
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS authorization_records (
        id VARCHAR PRIMARY KEY,
        patient_id VARCHAR NOT NULL,
        payer_name VARCHAR NOT NULL,
        auth_status VARCHAR NOT NULL
    );
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS payer_contracts (
        id VARCHAR PRIMARY KEY,
        tenant_id VARCHAR NOT NULL,
        payer_name VARCHAR NOT NULL,
        has_contract VARCHAR
    );
    """)


def downgrade() -> None:
    """
    Safe dev-only rollback
    """
    op.execute("DROP TABLE IF EXISTS payer_contracts;")
    op.execute("DROP TABLE IF EXISTS authorization_records;")
    op.execute("DROP TABLE IF EXISTS patient_payers;")
    op.execute("DROP TABLE IF EXISTS orders_snapshot;")
    op.execute("DROP TABLE IF EXISTS visit_minutes;")
    op.execute("DROP TABLE IF EXISTS continuous_care_events;")
    op.execute("DROP TABLE IF EXISTS respite_periods;")
    op.execute("DROP TABLE IF EXISTS gip_periods;")
    op.execute("DROP TABLE IF EXISTS patient_pos;")
    op.execute("DROP TABLE IF EXISTS billing_snapshot;")
    op.execute("DROP TABLE IF EXISTS billing_summary;")
    op.execute("DROP TABLE IF EXISTS billing_cycles;")