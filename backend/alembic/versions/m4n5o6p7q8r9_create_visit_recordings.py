"""create visit_recordings table

Adds a new, standalone table for visit audio recordings (capture + staff
review pipeline). Does not modify any existing table or data — this is an
additive migration only.

Revision ID: m4n5o6p7q8r9
Revises: l3m4n5o6p7q8
Create Date: 2026-08-19
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "m4n5o6p7q8r9"
down_revision = "l3m4n5o6p7q8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "visit_recordings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("visit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("visits.id", ondelete="CASCADE"), nullable=True),
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assessment_type", sa.String(32), nullable=True),
        sa.Column("recorded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("consent_confirmed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("consent_confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=True),
        sa.Column("mime_type", sa.String(64), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("transcript_status", sa.String(24), nullable=False, server_default=sa.text("'not_transcribed'")),
        sa.Column("transcript_provider", sa.String(32), nullable=True),
        sa.Column("transcript_text", sa.Text(), nullable=True),
        sa.Column("transcribed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
    )
    op.create_index("ix_visit_recordings_tenant_id", "visit_recordings", ["tenant_id"])
    op.create_index("ix_visit_recordings_patient_id", "visit_recordings", ["patient_id"])
    op.create_index("ix_visit_recordings_visit_id", "visit_recordings", ["visit_id"])
    op.create_index("ix_visit_recordings_assessment_id", "visit_recordings", ["assessment_id"])
    op.create_index("ix_visit_recordings_recorded_by", "visit_recordings", ["recorded_by"])


def downgrade() -> None:
    op.drop_index("ix_visit_recordings_recorded_by", table_name="visit_recordings")
    op.drop_index("ix_visit_recordings_assessment_id", table_name="visit_recordings")
    op.drop_index("ix_visit_recordings_visit_id", table_name="visit_recordings")
    op.drop_index("ix_visit_recordings_patient_id", table_name="visit_recordings")
    op.drop_index("ix_visit_recordings_tenant_id", table_name="visit_recordings")
    op.drop_table("visit_recordings")
