"""
add_admission_task_types_to_tasktype_enum

Adds CMS‑critical admission task types to tasks_task_type_enum.

Revision ID: 3b66961d337c
Revises: e7008e9b3d68
"""

from alembic import op

# ---------------------------------------------------------
# Alembic identifiers
# ---------------------------------------------------------
revision = "3b66961d337c"
down_revision = "e7008e9b3d68"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # RN Initial Assessment (<= 48h from SOC)
    op.execute(
        "ALTER TYPE tasks_task_type_enum ADD VALUE IF NOT EXISTS 'INITIAL_RN_ICA';"
    )

    # Notice of Election submission (<= 5 calendar days)
    op.execute(
        "ALTER TYPE tasks_task_type_enum ADD VALUE IF NOT EXISTS 'NOE_DUE';"
    )


def downgrade() -> None:
    # PostgreSQL enums cannot safely remove values.
    # Forward‑only by design for audit safety.
    pass
