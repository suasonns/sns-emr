"""patient identity hardening mrn ssn

Revision ID: 75b96f0ac8c6
Revises: 1f9f6baf1091
Create Date: 2026-05-31 10:32:39.769547

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# ✅ CORRECT REVISION IDENTIFIERS (DO NOT CHANGE)
revision: str = "75b96f0ac8c6"
down_revision: Union[str, Sequence[str], None] = "1f9f6baf1091"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """
    ✅ ENTERPRISE IDENTITY HARDENING (SAFE / IDEMPOTENT)

    - Add SSN last4 column
    - Add MRN index (if missing)
    - Add composite unique index (if missing)
    """

    # ✅ Add ssn_last4 column ONLY if it doesn't exist
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name='patients'
            AND column_name='ssn_last4'
        ) THEN
            ALTER TABLE patients ADD COLUMN ssn_last4 VARCHAR(4);
        END IF;
    END$$;
    """)

    # ✅ Create MRN index ONLY if it doesn't exist
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_indexes
            WHERE indexname = 'ix_patients_mrn'
        ) THEN
            CREATE INDEX ix_patients_mrn ON patients (mrn);
        END IF;
    END$$;
    """)

    # ✅ Create composite unique index ONLY if it doesn't exist
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_indexes
            WHERE indexname = 'uq_patients_tenant_mrn'
        ) THEN
            CREATE UNIQUE INDEX uq_patients_tenant_mrn
            ON patients (tenant_id, mrn);
        END IF;
    END$$;
    """)

def downgrade():
    """
    ⚠️ Optional rollback (not used in production forward-only systems)
    """

    op.drop_index("uq_patients_tenant_mrn", table_name="patients")
    op.drop_index("ix_patients_mrn", table_name="patients")
    op.drop_column("patients", "ssn_last4")