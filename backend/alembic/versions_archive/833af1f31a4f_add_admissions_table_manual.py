"""add admissions table manual

Revision ID: 833af1f31a4f
Revises: 67dd37c268ec
Create Date: 2026-07-16 11:17:17.583132

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '833af1f31a4f'
down_revision: Union[str, Sequence[str], None] = '67dd37c268ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS admissions (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            patient_id uuid NOT NULL,
            admission_date timestamp without time zone NOT NULL,
            status text NOT NULL DEFAULT 'DRAFT',
            created_at timestamp without time zone NOT NULL,
            created_by uuid NOT NULL,
            updated_at timestamp without time zone NULL,
            updated_by uuid NULL,
            attending_physician_id uuid NULL,
            referral_source text NULL,
            reason_for_admission text NULL,
            admission_authorized_at timestamp without time zone NULL,
            admission_authorized_by uuid NULL,
            soc_date timestamp without time zone NULL,
            soc_time timestamp without time zone NULL,
            effective_date timestamp with time zone NULL,
            election_signed_at timestamp with time zone NULL,
            certification_completed_at timestamp with time zone NULL,
            physician_order_signed_at timestamp with time zone NULL,
            initial_assessment_completed_at timestamp with time zone NULL,
            discharged_at timestamp with time zone NULL,
            discharge_reason text NULL,
            CONSTRAINT fk_admissions_patient_id
                FOREIGN KEY (patient_id)
                REFERENCES patients (id)
                ON DELETE CASCADE
        )
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_admissions_tenant_id
        ON admissions (tenant_id)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_admissions_patient_id
        ON admissions (patient_id)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_admissions_status
        ON admissions (status)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_admissions_created_by
        ON admissions (created_by)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_admissions_updated_by
        ON admissions (updated_by)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_admissions_admission_authorized_by
        ON admissions (admission_authorized_by)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_admissions_tenant_patient
        ON admissions (tenant_id, patient_id)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_admissions_tenant_patient")
    op.execute("DROP INDEX IF EXISTS ix_admissions_admission_authorized_by")
    op.execute("DROP INDEX IF EXISTS ix_admissions_updated_by")
    op.execute("DROP INDEX IF EXISTS ix_admissions_created_by")
    op.execute("DROP INDEX IF EXISTS ix_admissions_status")
    op.execute("DROP INDEX IF EXISTS ix_admissions_patient_id")
    op.execute("DROP INDEX IF EXISTS ix_admissions_tenant_id")
    op.execute("DROP TABLE IF EXISTS admissions")