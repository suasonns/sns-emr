"""enforce evidence on task completion

Revision ID: bba772574147
Revises: b7e1fce8435a
Create Date: 2026-06-01 17:07:44.101119
"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision: str = "bba772574147"
down_revision: Union[str, Sequence[str], None] = "b7e1fce8435a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Verification-only migration.

    Ensures that the database enforces evidence requirements
    for COMPLETED tasks via a CHECK constraint.

    This migration performs NO DDL and requires NO table ownership.
    """
    conn = op.get_bind()

    result = conn.execute(
        text(
            """
            SELECT 1
            FROM pg_constraint
            WHERE conname = 'ck_tasks_completed_requires_evidence';
            """
        )
    ).fetchone()

    if result is None:
        raise RuntimeError(
            "Expected CHECK constraint 'ck_tasks_completed_requires_evidence' "
            "does not exist on table tasks. "
            "Task completion evidence is NOT enforced at the database layer."
        )


def downgrade() -> None:
    """
    No-op downgrade.

    Constraint removal is intentionally not automated
    for compliance and audit safety.
    """
    pass