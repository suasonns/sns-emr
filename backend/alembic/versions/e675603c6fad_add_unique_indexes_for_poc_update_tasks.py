"""add unique indexes for POC_UPDATE tasks

Revision ID: e675603c6fad
Revises: 3e4fe81a0718
Create Date: 2026-05-01
"""

from alembic import op

revision = "e675603c6fad"
down_revision = "3e4fe81a0718"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_poc_update_manual_per_visit
        ON tasks (task_type, origin, completion_reference_type, completion_reference_id)
        WHERE task_type = 'POC_UPDATE'
          AND origin = 'MANUAL'
          AND completion_reference_type = 'VISIT';
        """
    )

    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_poc_update_periodic_per_patient_due
        ON tasks (task_type, origin, patient_id, due_date)
        WHERE task_type = 'POC_UPDATE'
          AND origin = 'PERIODIC';
        """
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS uq_poc_update_manual_per_visit;")
    op.execute("DROP INDEX IF EXISTS uq_poc_update_periodic_per_patient_due;")
