"""enforce unique initial RN ICA and NOE tasks

Revision ID: 3d7785acaf04
Revises: bf6f447fbe5e
Create Date: 2026-06-04
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3d7785acaf04"
down_revision: Union[str, Sequence[str], None] = "bf6f447fbe5e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Enforce strict uniqueness for initial onboarding tasks.

    Business rule (compliance-driven):
    - A patient may have only ONE INITIAL_RN_ICA task
    - A patient may have only ONE NOE_DUE task

    This is enforced via a partial unique index to avoid blocking
    legitimately recurring task types.
    """
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_tasks_initial_unique_per_patient
        ON tasks (tenant_id, patient_id, task_type)
        WHERE task_type IN ('INITIAL_RN_ICA', 'NOE_DUE');
        """
    )


def downgrade() -> None:
    """
    Remove uniqueness enforcement for initial onboarding tasks.
    (Dev/test rollback only; production should be forward-only.)
    """
    op.execute(
        """
        DROP INDEX IF EXISTS uq_tasks_initial_unique_per_patient;
        """
    )
