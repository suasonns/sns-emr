"""fix patient_assignments schema alignment

Revision ID: 52be2c0a3eaa
Revises: 1ba7178f0f4c
Create Date: 2026-06-22 23:21:35.504177

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '52be2c0a3eaa'
down_revision: Union[str, Sequence[str], None] = '1ba7178f0f4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # =========================================
    # 1. RENAME COLUMN staff_user_id → user_id
    # =========================================
    op.alter_column(
        "patient_assignments",
        "staff_user_id",
        new_column_name="user_id"
    )

    # =========================================
    # 2. CONVERT discipline → ENUM
    # =========================================

    op.execute("""
        ALTER TABLE patient_assignments
        ALTER COLUMN discipline TYPE assignment_discipline_enum
        USING discipline::text::assignment_discipline_enum
    """)


def downgrade():
    # reverse if needed
    op.alter_column(
        "patient_assignments",
        "user_id",
        new_column_name="staff_user_id"
    )

    op.execute("""
        ALTER TABLE patient_assignments
        ALTER COLUMN discipline TYPE VARCHAR(16)
    """)
