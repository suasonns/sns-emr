"""add cc_hourly_narrative_entries table

Revision ID: x8y9z0a1b2c3
Revises: w7x8y9z0a1b2
Create Date: 2026-08-23 13:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "x8y9z0a1b2c3"
down_revision = "w7x8y9z0a1b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cc_hourly_narrative_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("visit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("visits.id"), nullable=False),
        sa.Column("discipline", sa.String(32), nullable=False),
        sa.Column("entry_date", sa.String(16), nullable=True),
        sa.Column("entry_time", sa.String(16), nullable=True),
        sa.Column("temperature", sa.String(16), nullable=True),
        sa.Column("pulse", sa.String(16), nullable=True),
        sa.Column("respirations", sa.String(16), nullable=True),
        sa.Column("bp_systolic", sa.String(16), nullable=True),
        sa.Column("bp_diastolic", sa.String(16), nullable=True),
        sa.Column("o2_sat", sa.String(16), nullable=True),
        sa.Column("pain_level", sa.String(8), nullable=True),
        sa.Column("pain_location", sa.String(255), nullable=True),
        sa.Column("pain_intervention", sa.Text(), nullable=True),
        sa.Column("symptoms", sa.Text(), nullable=True),
        sa.Column("care_provided", sa.Text(), nullable=True),
        sa.Column("issue_identified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("issue_narrative", sa.Text(), nullable=True),
        sa.Column("poc_update_narrative", sa.Text(), nullable=True),
        sa.Column("narrative", sa.Text(), nullable=True),
        sa.Column("entered_by", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_cc_hourly_narrative_entries_tenant_id",
        "cc_hourly_narrative_entries",
        ["tenant_id"],
    )
    op.create_index(
        "ix_cc_hourly_narrative_entries_patient_id",
        "cc_hourly_narrative_entries",
        ["patient_id"],
    )
    op.create_index(
        "ix_cc_hourly_narrative_entries_visit_id",
        "cc_hourly_narrative_entries",
        ["visit_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_cc_hourly_narrative_entries_visit_id", table_name="cc_hourly_narrative_entries")
    op.drop_index("ix_cc_hourly_narrative_entries_patient_id", table_name="cc_hourly_narrative_entries")
    op.drop_index("ix_cc_hourly_narrative_entries_tenant_id", table_name="cc_hourly_narrative_entries")
    op.drop_table("cc_hourly_narrative_entries")
