"""create idg_meetings table

Revision ID: 79ead90226d9
Revises: dcecb916f4ed
Create Date: 2026-05-01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "79ead90226d9"
down_revision: Union[str, Sequence[str], None] = "dcecb916f4ed"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Drop the existing table (it exists but has the wrong schema)
    op.execute("DROP TABLE IF EXISTS public.idg_meetings CASCADE;")

    # Create the correct survey-defensible table
    op.create_table(
        "idg_meetings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("benefit_period_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("benefit_periods.id"), nullable=True),

        sa.Column("meeting_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="DRAFT"),
        sa.Column("finalized_at", sa.DateTime(), nullable=True),

        sa.Column("rn_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("physician_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("social_worker_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("chaplain_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),

        sa.Column("rn_present", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("physician_present", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("social_worker_present", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("chaplain_present", sa.Boolean(), nullable=False, server_default=sa.text("false")),

        sa.Column("summary", sa.Text(), nullable=True),

        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Add indexes explicitly (more reliable than index=True in Column for Alembic)

def downgrade():
    op.drop_table("idg_meetings")