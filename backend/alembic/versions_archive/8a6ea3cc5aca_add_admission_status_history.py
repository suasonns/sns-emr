"""add admission_status_history

Revision ID: 8a6ea3cc5aca
Revises: 833af1f31a4f
Create Date: 2026-07-16 11:31:22.931133

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a6ea3cc5aca'
down_revision: Union[str, Sequence[str], None] = '833af1f31a4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS admission_status_history (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            patient_id uuid NOT NULL,
            admission_id uuid NULL,
            previous_status text NULL,
            new_status text NOT NULL,
            changed_at timestamp without time zone NOT NULL,
            changed_by uuid NOT NULL,
            reason text NULL,
            notes text NULL,
            CONSTRAINT fk_adm_hist_patient
                FOREIGN KEY (patient_id)
                REFERENCES patients (id)
                ON DELETE CASCADE,
            CONSTRAINT fk_adm_hist_admission
                FOREIGN KEY (admission_id)
                REFERENCES admissions (id)
                ON DELETE SET NULL
        )
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_adm_hist_patient_id
        ON admission_status_history (patient_id)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_adm_hist_tenant_id
        ON admission_status_history (tenant_id)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_adm_hist_changed_at
        ON admission_status_history (changed_at)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_adm_hist_changed_by
        ON admission_status_history (changed_by)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_adm_hist_prev_new
        ON admission_status_history (previous_status, new_status)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_adm_hist_patient_time
        ON admission_status_history (patient_id, changed_at)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_adm_hist_patient_time")
    op.execute("DROP INDEX IF EXISTS ix_adm_hist_prev_new")
    op.execute("DROP INDEX IF EXISTS ix_adm_hist_changed_by")
    op.execute("DROP INDEX IF EXISTS ix_adm_hist_changed_at")
    op.execute("DROP INDEX IF EXISTS ix_adm_hist_tenant_id")
    op.execute("DROP INDEX IF EXISTS ix_adm_hist_patient_id")
    op.execute("DROP TABLE IF EXISTS admission_status_history")