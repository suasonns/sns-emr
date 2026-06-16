"""enforce_task_completion_requires_evidence

Revision ID: e216a77a1e11
Revises: 3d7785acaf04
Create Date: 2026-06-04 14:53:46

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e216a77a1e11"
down_revision: Union[str, Sequence[str], None] = "3d7785acaf04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Enforce evidence + timestamp when a task is marked COMPLETED.

    Guarded to be idempotent:
    - If the constraint already exists, do nothing
    - Otherwise, create it
    """
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'ck_tasks_completed_requires_evidence'
            ) THEN
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
            END IF;
        END
        $$;
        """
    )

def downgrade() -> None:
    """
    Forward-only system.

    Downgrade explicitly removes the CHECK constraint
    (used only for controlled rollback scenarios).
    """
    op.execute(
        """
        ALTER TABLE tasks
        DROP CONSTRAINT IF EXISTS ck_tasks_completed_requires_evidence
        """
    )