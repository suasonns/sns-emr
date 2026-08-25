"""add post_death_bereavement_assessments table

Revision ID: 5d1c9a3e7f2b
Revises: e0f45baa4ec0
Create Date: 2026-08-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "5d1c9a3e7f2b"
down_revision = "e0f45baa4ec0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "post_death_bereavement_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("status", sa.String(16), nullable=False, index=True),
        sa.Column("bereavement_assessment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bereavement_assessments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("bereavement_poc_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bereavement_pocs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("entered_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("staff_assigned", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("discipline", sa.String(16), nullable=True),
        sa.Column("visit_type", sa.String(16), nullable=True),
        sa.Column("visit_mode", sa.String(16), nullable=True),
        sa.Column("visit_date", sa.Date(), nullable=True),
        sa.Column("time_in", sa.String(8), nullable=True),
        sa.Column("time_out", sa.String(8), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("no_family", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("primary_first_name", sa.String(128), nullable=True),
        sa.Column("primary_last_name", sa.String(128), nullable=True),
        sa.Column("primary_relationship_to_patient", sa.String(128), nullable=True),
        sa.Column("primary_address", sa.String(255), nullable=True),
        sa.Column("primary_city", sa.String(128), nullable=True),
        sa.Column("primary_state", sa.String(64), nullable=True),
        sa.Column("primary_zip", sa.String(16), nullable=True),
        sa.Column("primary_home_phone", sa.String(32), nullable=True),
        sa.Column("primary_cell_phone", sa.String(32), nullable=True),
        sa.Column("primary_email", sa.String(255), nullable=True),
        sa.Column("primary_was_caregiver", sa.Boolean(), nullable=True),
        sa.Column("date_of_death", sa.Date(), nullable=True),
        sa.Column("place_of_death", sa.String(32), nullable=True),
        sa.Column("death_expected", sa.Boolean(), nullable=True),
        sa.Column("pcg_present_at_death", sa.Boolean(), nullable=True),
        sa.Column("family_present_at_death", sa.Boolean(), nullable=True),
        sa.Column("funeral_plans_finalized", sa.Boolean(), nullable=True),
        sa.Column("funeral_home_name", sa.String(255), nullable=True),
        sa.Column("condolence_call_date", sa.Date(), nullable=True),
        sa.Column("condolence_call_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("condolence_call_notes", sa.Text(), nullable=True),
        sa.Column("emotional_status_narrative", sa.Text(), nullable=True),
        sa.Column("survivor_support_system_adequate", sa.Boolean(), nullable=True),
        sa.Column("desires_intensive_bereavement_support", sa.Boolean(), nullable=True),
        sa.Column("complicated_grief_reactions_observed", sa.Boolean(), nullable=True),
        sa.Column("additional_risk_factors_since_initial", sa.Boolean(), nullable=True),
        sa.Column("additional_risk_notes", sa.Text(), nullable=True),
        sa.Column("risk_items", postgresql.JSONB(), nullable=False),
        sa.Column("risk_other_note", sa.Text(), nullable=True),
        sa.Column("risk_total_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("risk_level", sa.String(16), nullable=True),
        sa.Column("goals", postgresql.JSONB(), nullable=False),
        sa.Column("interventions", postgresql.JSONB(), nullable=False),
        sa.Column("other_interventions", sa.Text(), nullable=True),
        sa.Column("plan_of_care_narrative", sa.Text(), nullable=True),
        sa.Column("narrative", sa.Text(), nullable=True),
        sa.Column("signed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("post_death_bereavement_assessments")
