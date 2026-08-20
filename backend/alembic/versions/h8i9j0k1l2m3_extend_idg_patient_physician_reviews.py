"""extend idg_patient_physician_reviews with audit trail + checklist fields

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-08-19 11:45:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "h8i9j0k1l2m3"
down_revision = "g7h8i9j0k1l2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "idg_patient_physician_reviews",
        sa.Column("recorded_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "idg_patient_physician_reviews",
        sa.Column("reviewed_by_physician_directly", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column(
        "idg_patient_physician_reviews",
        sa.Column("review_source", sa.String(length=30), server_default=sa.text("'IDG'"), nullable=False),
    )
    op.add_column(
        "idg_patient_physician_reviews",
        sa.Column("defer_reason", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "idg_patient_physician_reviews",
        sa.Column("defer_note", sa.Text(), nullable=True),
    )
    op.add_column(
        "idg_patient_physician_reviews",
        sa.Column("poc_reviewed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column(
        "idg_patient_physician_reviews",
        sa.Column("medication_list_reviewed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column(
        "idg_patient_physician_reviews",
        sa.Column("medication_reconciliation_reviewed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column(
        "idg_patient_physician_reviews",
        sa.Column("orders_reviewed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column(
        "idg_patient_physician_reviews",
        sa.Column("discussion_reviewed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )

    op.alter_column("idg_patient_physician_reviews", "review_status", server_default=sa.text("'PENDING'"))
    op.alter_column("idg_patient_physician_reviews", "reviewed_at", nullable=True, server_default=None)

    op.create_index(
        "ix_idg_ppr_recorded_by_user_id", "idg_patient_physician_reviews", ["recorded_by_user_id"]
    )


def downgrade():
    op.drop_index("ix_idg_ppr_recorded_by_user_id", table_name="idg_patient_physician_reviews")

    op.alter_column("idg_patient_physician_reviews", "reviewed_at", nullable=False, server_default=sa.text("NOW()"))
    op.alter_column("idg_patient_physician_reviews", "review_status", server_default=None)

    op.drop_column("idg_patient_physician_reviews", "discussion_reviewed")
    op.drop_column("idg_patient_physician_reviews", "orders_reviewed")
    op.drop_column("idg_patient_physician_reviews", "medication_reconciliation_reviewed")
    op.drop_column("idg_patient_physician_reviews", "medication_list_reviewed")
    op.drop_column("idg_patient_physician_reviews", "poc_reviewed")
    op.drop_column("idg_patient_physician_reviews", "defer_note")
    op.drop_column("idg_patient_physician_reviews", "defer_reason")
    op.drop_column("idg_patient_physician_reviews", "review_source")
    op.drop_column("idg_patient_physician_reviews", "reviewed_by_physician_directly")
    op.drop_column("idg_patient_physician_reviews", "recorded_by_user_id")
