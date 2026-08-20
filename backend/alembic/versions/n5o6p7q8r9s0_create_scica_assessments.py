"""create scica_assessments table

Revision ID: n5o6p7q8r9s0
Revises: m4n5o6p7q8r9
Create Date: 2026-08-19
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "n5o6p7q8r9s0"
down_revision = "m4n5o6p7q8r9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scica_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("visit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("visits.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assessment_type", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("locked", sa.Boolean(), nullable=False),
        sa.Column("form_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_scica_assessments_patient_id"), "scica_assessments", ["patient_id"], unique=False)
    op.create_index(op.f("ix_scica_assessments_visit_id"), "scica_assessments", ["visit_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_scica_assessments_visit_id"), table_name="scica_assessments")
    op.drop_index(op.f("ix_scica_assessments_patient_id"), table_name="scica_assessments")
    op.drop_table("scica_assessments")
