"""Add benefit periods table

Revision ID: b677e343f59f
Revises: efb85249ff6a
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "b677e343f59f"
down_revision = "efb85249ff6a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "benefit_periods",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", UUID(as_uuid=True), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("benefit_number", sa.Integer, nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    op.create_index("idx_benefit_periods_patient", "benefit_periods", ["patient_id"])
    op.create_index("idx_benefit_periods_dates", "benefit_periods", ["start_date", "end_date"])
    op.create_index("idx_benefit_periods_current", "benefit_periods", ["is_current"])


def downgrade() -> None:
    op.drop_index("idx_benefit_periods_current", table_name="benefit_periods")
    op.drop_index("idx_benefit_periods_dates", table_name="benefit_periods")
    op.drop_index("idx_benefit_periods_patient", table_name="benefit_periods")
    op.drop_table("benefit_periods")