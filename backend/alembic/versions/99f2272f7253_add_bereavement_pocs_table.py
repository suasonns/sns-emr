"""add bereavement_pocs table

Revision ID: 99f2272f7253
Revises: 39a3ecfb64ad
Create Date: 2026-08-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "99f2272f7253"
down_revision = "39a3ecfb64ad"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bereavement_pocs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("bereavement_assessment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bereavement_assessments.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("status", sa.String(16), nullable=False, index=True),
        sa.Column("entered_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("staff_assigned", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("discipline", sa.String(16), nullable=True),
        sa.Column("date_of_death", sa.Date(), nullable=True),
        sa.Column("risk_level", sa.String(16), nullable=True),
        sa.Column("goals", postgresql.JSONB(), nullable=False),
        sa.Column("interventions", postgresql.JSONB(), nullable=False),
        sa.Column("action_plan", postgresql.JSONB(), nullable=False),
        sa.Column("narrative", sa.Text(), nullable=True),
        sa.Column("closed_early", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("closed_reason", sa.Text(), nullable=True),
        sa.Column("signed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("bereavement_pocs")
