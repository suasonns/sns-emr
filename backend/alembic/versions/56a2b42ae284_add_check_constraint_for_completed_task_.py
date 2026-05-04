"""add check constraint for completed task evidence

Revision ID: 56a2b42ae284
Revises: e675603c6fad
Create Date: 2026-05-01
"""

from alembic import op

revision = "56a2b42ae284"
down_revision = "e675603c6fad"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        ALTER TABLE tasks
        ADD CONSTRAINT ck_tasks_completed_requires_evidence
        CHECK (
            status <> 'COMPLETED'
            OR (
                completed_at IS NOT NULL
                AND completion_reference_type IS NOT NULL
                AND completion_reference_id IS NOT NULL
            )
        );
        """
    )


def downgrade():
    op.execute(
        """
        ALTER TABLE tasks
        DROP CONSTRAINT IF EXISTS ck_tasks_completed_requires_evidence;
        """
    )