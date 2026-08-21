"""add hospice snapshot fields to patient_facesheet

Revision ID: p7q8r9s0t1u2
Revises: o6p7q8r9s0t1
Create Date: 2026-08-21 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "p7q8r9s0t1u2"
down_revision = "o6p7q8r9s0t1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("patient_facesheet", sa.Column("election_date", sa.Date(), nullable=True))
    op.add_column("patient_facesheet", sa.Column("face_to_face_due_date", sa.Date(), nullable=True))
    op.add_column("patient_facesheet", sa.Column("benefit_period_number", sa.String(), nullable=True))
    op.add_column("patient_facesheet", sa.Column("benefit_period_start", sa.Date(), nullable=True))
    op.add_column("patient_facesheet", sa.Column("benefit_period_end", sa.Date(), nullable=True))
    op.add_column("patient_facesheet", sa.Column("pps_score", sa.String(), nullable=True))
    op.add_column("patient_facesheet", sa.Column("kps_score", sa.String(), nullable=True))
    op.add_column("patient_facesheet", sa.Column("fast_stage", sa.String(), nullable=True))
    op.add_column("patient_facesheet", sa.Column("code_status", sa.String(), nullable=True))
    op.add_column("patient_facesheet", sa.Column("cti_status", sa.String(), nullable=True))
    op.add_column("patient_facesheet", sa.Column("noe_status", sa.String(), nullable=True))
    op.add_column("patient_facesheet", sa.Column("primary_rn_name", sa.String(), nullable=True))
    op.add_column("patient_facesheet", sa.Column("social_worker_name", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("patient_facesheet", "social_worker_name")
    op.drop_column("patient_facesheet", "primary_rn_name")
    op.drop_column("patient_facesheet", "noe_status")
    op.drop_column("patient_facesheet", "cti_status")
    op.drop_column("patient_facesheet", "code_status")
    op.drop_column("patient_facesheet", "fast_stage")
    op.drop_column("patient_facesheet", "kps_score")
    op.drop_column("patient_facesheet", "pps_score")
    op.drop_column("patient_facesheet", "benefit_period_end")
    op.drop_column("patient_facesheet", "benefit_period_start")
    op.drop_column("patient_facesheet", "benefit_period_number")
    op.drop_column("patient_facesheet", "face_to_face_due_date")
    op.drop_column("patient_facesheet", "election_date")
