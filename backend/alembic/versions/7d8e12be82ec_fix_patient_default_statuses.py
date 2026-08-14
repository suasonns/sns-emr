"""
fix_patient_default_statuses

Revision ID: 7d8e12be82ec
Revises: a8ec3016df7b
Create Date: 2026-08-13 02:20:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "7d8e12be82ec"
down_revision: Union[str, Sequence[str], None] = "a8ec3016df7b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE patients SET status = 'ACTIVE' WHERE status IS NULL;"
        )
    )
    op.execute(
        sa.text(
            "UPDATE patients SET admission_status = 'PRE_REFERRAL' WHERE admission_status IS NULL;"
        )
    )
    op.execute(
        sa.text(
            "UPDATE patients SET acuity_state = 'ROUTINE' WHERE acuity_state IS NULL;"
        )
    )

    op.execute(
        sa.text(
            "ALTER TABLE patients ALTER COLUMN status SET DEFAULT 'ACTIVE';"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE patients ALTER COLUMN admission_status SET DEFAULT 'PRE_REFERRAL';"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE patients ALTER COLUMN acuity_state SET DEFAULT 'ROUTINE';"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "ALTER TABLE patients ALTER COLUMN status DROP DEFAULT;"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE patients ALTER COLUMN admission_status DROP DEFAULT;"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE patients ALTER COLUMN acuity_state DROP DEFAULT;"
        )
    )
