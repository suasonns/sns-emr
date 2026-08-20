"""add idg_patient_physician_reviews table

Revision ID: a1b2c3d4e5f6
Revises: f6a7b8c9d0e1
Create Date: 2026-08-19 11:15:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "g7h8i9j0k1l2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "idg_patient_physician_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("idg_meeting_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("physician_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("review_status", sa.String(length=20), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("batch_signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["idg_meeting_id"], ["idg_meetings.id"]),
        sa.UniqueConstraint("idg_meeting_id", "patient_id", name="uq_idg_patient_physician_review_session_patient"),
    )
    op.create_index("ix_idg_ppr_tenant_id", "idg_patient_physician_reviews", ["tenant_id"])
    op.create_index("ix_idg_ppr_patient_id", "idg_patient_physician_reviews", ["patient_id"])
    op.create_index("ix_idg_ppr_idg_meeting_id", "idg_patient_physician_reviews", ["idg_meeting_id"])
    op.create_index("ix_idg_ppr_physician_user_id", "idg_patient_physician_reviews", ["physician_user_id"])
    op.create_index("ix_idg_ppr_review_status", "idg_patient_physician_reviews", ["review_status"])


def downgrade():
    op.drop_index("ix_idg_ppr_review_status", table_name="idg_patient_physician_reviews")
    op.drop_index("ix_idg_ppr_physician_user_id", table_name="idg_patient_physician_reviews")
    op.drop_index("ix_idg_ppr_idg_meeting_id", table_name="idg_patient_physician_reviews")
    op.drop_index("ix_idg_ppr_patient_id", table_name="idg_patient_physician_reviews")
    op.drop_index("ix_idg_ppr_tenant_id", table_name="idg_patient_physician_reviews")
    op.drop_table("idg_patient_physician_reviews")
