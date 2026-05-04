"""add acuity_state_at_visit to visits

Revision ID: 5415a8ee619c
Revises: 7d3568b68e67
Create Date: 2026-05-03 14:43:38.430569

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5415a8ee619c'
down_revision: Union[str, Sequence[str], None] = '7d3568b68e67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add acuity_state_at_visit to visits to preserve
    the patient's acuity context at time of visit.
    """

    # 1) Add nullable column (safe rollout)
    op.add_column(
        "visits",
        sa.Column("acuity_state_at_visit", sa.String(length=32), nullable=True),
    )

    # 2) Best-effort backfill from patients table
    #    This ensures historical visits have a reasonable baseline
    op.execute(
        """
        UPDATE visits v
        SET acuity_state_at_visit = p.acuity_state
        FROM patients p
        WHERE v.patient_id = p.id
          AND v.acuity_state_at_visit IS NULL
          AND p.acuity_state IS NOT NULL
        """
    )

    # 3) Optional index for filtering/reporting
    op.create_index(
        "ix_visits_acuity_state_at_visit",
        "visits",
        ["acuity_state_at_visit"],
        unique=False,
    )


def downgrade() -> None:
    """
    Remove acuity_state_at_visit from visits.
    """
    op.drop_index(
        "ix_visits_acuity_state_at_visit",
        table_name="visits",
    )
    op.drop_column("visits", "acuity_state_at_visit")