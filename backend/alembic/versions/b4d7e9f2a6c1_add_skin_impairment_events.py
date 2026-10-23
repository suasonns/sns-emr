"""add skin_impairment_events longitudinal event log

Revision ID: b4d7e9f2a6c1
Revises: f3a9b2c7d1e4
Create Date: 2026-11-21

PRODUCT OWNER DIRECTIVE "Longitudinal Wound Record" -- append-only event
log for one SkinImpairment: assessment/treatment/photo/status_change/coc/
resolution/reopened events, designed so a future clinical-decision-support
feature can analyze wound trajectories without re-parsing historical
RNICA form_data JSONB. No recommendation/interpretation logic is added in
this migration or phase -- structure only.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b4d7e9f2a6c1"
down_revision = "f3a9b2c7d1e4"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "skin_impairment_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("skin_impairment_id", sa.String(length=64), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("visit_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=True),
        sa.Column(
            "recorded_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("recorded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("recorded_by_discipline", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=True),
        sa.Column("previous_status", sa.String(length=16), nullable=True),
        sa.Column("stage", sa.String(length=64), nullable=True),
        sa.Column("measurement_length_cm", sa.Numeric(6, 2), nullable=True),
        sa.Column("measurement_width_cm", sa.Numeric(6, 2), nullable=True),
        sa.Column("measurement_depth_cm", sa.Numeric(6, 2), nullable=True),
        sa.Column("drainage_amount", sa.String(length=32), nullable=True),
        sa.Column("drainage_character", sa.String(length=64), nullable=True),
        sa.Column("odor", sa.String(length=32), nullable=True),
        sa.Column("surrounding_skin", sa.String(length=64), nullable=True),
        sa.Column("treatment_summary", sa.Text(), nullable=True),
        sa.Column("photo_id", sa.String(length=64), nullable=False, server_default=sa.text("''")),
        sa.Column("coc_reason", sa.Text(), nullable=True),
        sa.Column("resolution_reason", sa.String(length=64), nullable=True),
        sa.Column("resolution_narrative", sa.Text(), nullable=True),
        sa.Column("poc_change_summary", sa.Text(), nullable=True),
        sa.Column("provider_notified", sa.Boolean(), nullable=True),
        sa.Column("provider_notified_name", sa.String(length=128), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["skin_impairment_id"], ["skin_impairments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["visit_id"], ["visits.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assessment_id"], ["rnica_assessments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["recorded_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_skin_impairment_events_impairment_id", "skin_impairment_events", ["skin_impairment_id"]
    )
    op.create_index(
        "ix_skin_impairment_events_tenant_id", "skin_impairment_events", ["tenant_id"]
    )
    op.create_index(
        "ix_skin_impairment_events_patient_id", "skin_impairment_events", ["patient_id"]
    )
    op.create_index(
        "ix_skin_impairment_events_event_type", "skin_impairment_events", ["event_type"]
    )
    op.create_index(
        "ix_skin_impairment_events_impairment_date",
        "skin_impairment_events", ["skin_impairment_id", "event_date"],
    )
    op.create_index(
        "ix_skin_impairment_events_tenant_patient_type",
        "skin_impairment_events", ["tenant_id", "patient_id", "event_type"],
    )
    op.create_index(
        "uq_skin_impairment_events_natural_key",
        "skin_impairment_events",
        ["skin_impairment_id", "assessment_id", "event_type", "photo_id"],
        unique=True,
    )


def downgrade():
    op.drop_table("skin_impairment_events")
