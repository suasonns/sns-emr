"""add_patient_insurances_table

Revision ID: 9d4fccab1558
Revises: f35a48856e72
Create Date: 2026-05-31

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "9d4fccab1558"
down_revision: Union[str, Sequence[str], None] = "f35a48856e72"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_name = 'patient_insurances'
            ) THEN

                CREATE TABLE patient_insurances (
                    id UUID PRIMARY KEY,
                    tenant_id UUID NOT NULL,
                    patient_id UUID NOT NULL,

                    payer_type VARCHAR(32) NOT NULL,
                    payer_name VARCHAR(255) NOT NULL,

                    subscriber_id VARCHAR(128) NOT NULL,
                    subscriber_id_type VARCHAR(32),

                    group_number VARCHAR(128),

                    coverage_scope VARCHAR(32) NOT NULL,
                    priority_order INTEGER NOT NULL,

                    is_active BOOLEAN NOT NULL DEFAULT TRUE,

                    effective_date DATE,
                    end_date DATE,

                    notes TEXT,

                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE INDEX idx_patient_insurances_tenant_id
                    ON patient_insurances (tenant_id);

                CREATE INDEX idx_patient_insurances_patient_id
                    ON patient_insurances (patient_id);

                CREATE INDEX idx_patient_insurances_scope
                    ON patient_insurances (coverage_scope);

                CREATE INDEX idx_patient_insurances_active
                    ON patient_insurances (is_active);

            END IF;
        END$$;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS patient_insurances;")
