"""add missing columns to patient_assignments

Revision ID: 0302a7da9571
Revises: 3763e76df09c
Create Date: 2026-06-23 14:47:00.414139

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0302a7da9571'
down_revision: Union[str, Sequence[str], None] = '3763e76df09c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # ✅ Add is_primary column
    op.add_column(
        "patient_assignments",
        sa.Column(
            "is_primary",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    # ✅ Add active column
    op.add_column(
        "patient_assignments",
        sa.Column(
            "active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )

    # ✅ Optional cleanup: remove defaults after backfill
    op.alter_column(
        "patient_assignments",
        "is_primary",
        server_default=None,
    )

    op.alter_column(
        "patient_assignments",
        "active",
        server_default=None,
    )


def downgrade():
    op.drop_column("patient_assignments", "active")
    op.drop_column("patient_assignments", "is_primary")