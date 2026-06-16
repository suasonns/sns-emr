"""add ICA task types

Revision ID: 33247aa788ef
Revises: 9987dfe1a87e
Create Date: 2026-06-01 14:50:48.387820

Adds ICA-related task types to tasks_task_type_enum.
Forward-only migration (ENUM values cannot be removed).
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "33247aa788ef"
down_revision = "9987dfe1a87e"
branch_labels = None
depends_on = None


ICA_TASK_TYPES = [
    "INITIAL_RN_ICA",
    "INITIAL_MSW_ICA",
    "INITIAL_SC_ICA",
    "INITIAL_BEREAVEMENT",
]


def upgrade() -> None:
    for task_type in ICA_TASK_TYPES:
        op.execute(
            f"ALTER TYPE tasks_task_type_enum ADD VALUE IF NOT EXISTS '{task_type}'"
        )


def downgrade() -> None:
    # PostgreSQL ENUM values cannot be safely removed.
    # This migration is intentionally forward-only.
    pass