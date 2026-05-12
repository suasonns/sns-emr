"""add previous_hope_record_id to hope_records

Revision ID: 496930c6a3ba
Revises: 3a4f0af44d73
Create Date: 2026-05-04 14:59:01.235178

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '496930c6a3ba'
down_revision: Union[str, Sequence[str], None] = '3a4f0af44d73'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure table exists (minimal skeleton)
    op.execute("""
    DO $$
    BEGIN
      IF to_regclass('public.hope_records') IS NULL THEN
        -- Minimal HOPE table skeleton (safe for later expansion)
        CREATE TABLE public.hope_records (
          id UUID PRIMARY KEY,
          patient_id UUID NULL,
          created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
          updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
        );

        -- Add FK to patients only if patients exists (it should by now)
        IF to_regclass('public.patients') IS NOT NULL THEN
          ALTER TABLE public.hope_records
            ADD CONSTRAINT hope_records_patient_id_fkey
            FOREIGN KEY (patient_id) REFERENCES public.patients(id);
        END IF;
      END IF;
    END $$;
    """)

    # Add column safely
    op.execute("""
    ALTER TABLE public.hope_records
      ADD COLUMN IF NOT EXISTS previous_hope_record_id UUID;
    """)

    # Add self-referencing FK only if not already present
    op.execute("""
    DO $$
    BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'hope_records_previous_hope_record_id_fkey'
      ) THEN
        ALTER TABLE public.hope_records
          ADD CONSTRAINT hope_records_previous_hope_record_id_fkey
          FOREIGN KEY (previous_hope_record_id) REFERENCES public.hope_records(id);
      END IF;
    END $$;
    """)

def downgrade():
    op.drop_constraint(
        "fk_hope_records_previous",
        "hope_records",
        type_="foreignkey",
    )

    op.drop_column(
        "hope_records",
        "previous_hope_record_id",
    )