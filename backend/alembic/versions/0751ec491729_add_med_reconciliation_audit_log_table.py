"""
add med reconciliation audit log table

Revision ID: 0751ec491729
Revises: 78b1046dc82c
Create Date: 2026-06-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0751ec491729"
down_revision = "78b1046dc82c"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "med_reconciliation_audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("import_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=True),

        sa.Column("stage", sa.String(length=50), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),

        sa.Column("med_name_raw", sa.String(length=255), nullable=True),

        sa.Column("input_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("normalized_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("comparison_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("decision_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_index(
        "ix_med_recon_audit_logs_patient_id",
        "med_reconciliation_audit_logs",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        "ix_med_recon_audit_logs_import_id",
        "med_reconciliation_audit_logs",
        ["import_id"],
        unique=False,
    )
    op.create_index(
        "ix_med_recon_audit_logs_item_id",
        "med_reconciliation_audit_logs",
        ["item_id"],
        unique=False,
    )
    op.create_index(
        "ix_med_recon_audit_logs_stage_event",
        "med_reconciliation_audit_logs",
        ["stage", "event_type"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_med_recon_audit_logs_stage_event", table_name="med_reconciliation_audit_logs")
    op.drop_index("ix_med_recon_audit_logs_item_id", table_name="med_reconciliation_audit_logs")
    op.drop_index("ix_med_recon_audit_logs_import_id", table_name="med_reconciliation_audit_logs")
    op.drop_index("ix_med_recon_audit_logs_patient_id", table_name="med_reconciliation_audit_logs")
    op.drop_table("med_reconciliation_audit_logs")