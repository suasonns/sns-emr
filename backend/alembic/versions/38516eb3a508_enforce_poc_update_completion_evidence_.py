from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "38516eb3a508"
down_revision: Union[str, Sequence[str], None] = "34064ee66034"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Non-completed tasks must not carry completion evidence
    op.execute("""
    UPDATE tasks
    SET
      completed_at = NULL,
      completion_reference_type = NULL,
      completion_reference_id = NULL
    WHERE status <> 'COMPLETED'
      AND (
        completed_at IS NOT NULL
        OR completion_reference_type IS NOT NULL
        OR completion_reference_id IS NOT NULL
      );
    """)

    # 2) Completed tasks must have completed_at
    op.execute("""
    UPDATE tasks
    SET completed_at = COALESCE(updated_at, created_at, NOW())
    WHERE status = 'COMPLETED'
      AND completed_at IS NULL;
    """)

    # 3) Completed tasks must have completion evidence; otherwise revert to pending
    op.execute("""
    UPDATE tasks
    SET
      status = 'PENDING',
      completed_at = NULL,
      completion_reference_type = NULL,
      completion_reference_id = NULL
    WHERE status = 'COMPLETED'
      AND (
        completion_reference_type IS NULL
        OR completion_reference_id IS NULL
      );
    """)

    # 4) If a partial constraint exists from a prior attempt, remove it safely
    op.execute("""
    ALTER TABLE tasks
    DROP CONSTRAINT IF EXISTS tasks_completion_evidence_consistency;
    """)

    # 5) Add the constraint
    op.execute("""
    ALTER TABLE tasks
    ADD CONSTRAINT tasks_completion_evidence_consistency
    CHECK (
      (
        status = 'COMPLETED'
        AND completed_at IS NOT NULL
        AND completion_reference_type IS NOT NULL
        AND completion_reference_id IS NOT NULL
      )
      OR
      (
        status <> 'COMPLETED'
        AND completed_at IS NULL
        AND completion_reference_type IS NULL
        AND completion_reference_id IS NULL
      )
    );
    """)

def downgrade() -> None:
    """
    Remove completion evidence consistency constraint.
    """
    op.execute(
        """
        ALTER TABLE tasks
        DROP CONSTRAINT IF EXISTS tasks_completion_evidence_consistency
        """
    )
