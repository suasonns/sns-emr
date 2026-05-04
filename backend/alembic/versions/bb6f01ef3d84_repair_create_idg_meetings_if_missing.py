"""repair create idg_meetings if missing

Revision ID: bb6f01ef3d84
Revises: 79ead90226d9
Create Date: 2026-05-01 07:23:03.359131
"""

from typing import Sequence, Union
from alembic import op


# Alembic revision identifiers
revision: str = "bb6f01ef3d84"
down_revision: Union[str, Sequence[str], None] = "79ead90226d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    sql = """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = 'idg_meetings'
        ) THEN
            CREATE TABLE public.idg_meetings (
                id UUID PRIMARY KEY,
                patient_id UUID NOT NULL REFERENCES patients(id),
                benefit_period_id UUID NULL REFERENCES benefit_periods(id),

                meeting_date DATE NOT NULL,
                status VARCHAR NOT NULL DEFAULT 'DRAFT',
                finalized_at TIMESTAMP NULL,

                rn_required BOOLEAN NOT NULL DEFAULT true,
                physician_required BOOLEAN NOT NULL DEFAULT true,
                social_worker_required BOOLEAN NOT NULL DEFAULT false,
                chaplain_required BOOLEAN NOT NULL DEFAULT false,

                rn_present BOOLEAN NOT NULL DEFAULT false,
                physician_present BOOLEAN NOT NULL DEFAULT false,
                social_worker_present BOOLEAN NOT NULL DEFAULT false,
                chaplain_present BOOLEAN NOT NULL DEFAULT false,

                summary TEXT NULL,

                created_at TIMESTAMP NOT NULL DEFAULT now(),
                updated_at TIMESTAMP NOT NULL DEFAULT now(),
                created_by UUID NULL
            );

            CREATE INDEX IF NOT EXISTS ix_idg_meetings_patient_id
                ON public.idg_meetings(patient_id);

            CREATE INDEX IF NOT EXISTS ix_idg_meetings_benefit_period_id
                ON public.idg_meetings(benefit_period_id);

            CREATE INDEX IF NOT EXISTS ix_idg_meetings_meeting_date
                ON public.idg_meetings(meeting_date);
        END IF;
    END$$;
    """
    op.execute(sql)


def downgrade():
    # Forward-only repair migration
    pass
