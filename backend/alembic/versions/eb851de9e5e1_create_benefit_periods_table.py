"""create benefit periods table

Revision ID: eb851de9e5e1
Revises: 924041973331
Create Date: 2026-04-30 12:40:19.663958
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "eb851de9e5e1"
down_revision = "924041973331"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Safety-first migration:
    - If benefit_periods already exists (created by b677e343f59f), do nothing.
    - Otherwise create a minimal benefit_periods table WITHOUT depending on users.
    - NEVER drop tasks here.
    """
    bind = op.get_bind()

    # If already exists, no-op
    exists = bind.execute(sa.text("SELECT to_regclass('public.benefit_periods')")).scalar()
    if exists:
        return

    op.create_table(
        "benefit_periods",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),

        sa.Column("patient_id", UUID(as_uuid=True), sa.ForeignKey("patients.id"), nullable=False),

        # Benefit period sequence number for patient (1,2,3...)
        sa.Column("benefit_number", sa.Integer, nullable=False),

        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=True),

        # helper flag; true means active period
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.text("false")),

        # audit timestamps (no users dependency)
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),

        # Keep created_by as UUID without FK so it never blocks install order
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
    )

    op.create_index("ix_benefit_periods_patient_id", "benefit_periods", ["patient_id"], unique=False)
    op.create_index("ix_benefit_periods_start_date", "benefit_periods", ["start_date"], unique=False)
    op.create_index("ix_benefit_periods_end_date", "benefit_periods", ["end_date"], unique=False)
    op.create_index("ix_benefit_periods_is_current", "benefit_periods", ["is_current"], unique=False)


def downgrade() -> None:
    # Safe rollback for dev only
    op.drop_index("ix_benefit_periods_is_current", table_name="benefit_periods")
    op.drop_index("ix_benefit_periods_end_date", table_name="benefit_periods")
    op.drop_index("ix_benefit_periods_start_date", table_name="benefit_periods")
    op.drop_index("ix_benefit_periods_patient_id", table_name="benefit_periods")
    op.drop_table("benefit_periods")