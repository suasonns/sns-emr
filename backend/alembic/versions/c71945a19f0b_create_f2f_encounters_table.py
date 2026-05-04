"""create f2f_encounters table

Revision ID: c71945a19f0b
Revises: 5cc577fb901e
Create Date: 2026-05-01 09:49:56.501962
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "c71945a19f0b"
down_revision: Union[str, Sequence[str], None] = "5cc577fb901e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "f2f_encounters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),

        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "benefit_period_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("benefit_periods.id"),
            nullable=False,
            index=True,
        ),

        sa.Column("encounter_date", sa.Date(), nullable=False),
        sa.Column("performed_by_role", sa.String(), nullable=False),  # MD or NP
        sa.Column("performed_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),

        sa.Column("summary", sa.Text(), nullable=True),

        sa.Column("status", sa.String(), nullable=False, server_default="DRAFT"),
        sa.Column("finalized_at", sa.DateTime(), nullable=True),

        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("f2f_encounters")
