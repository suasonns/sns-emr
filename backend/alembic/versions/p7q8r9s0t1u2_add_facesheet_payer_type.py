"""add patient_facesheet payer source type columns for HOPE A1400

Revision ID: p7q8r9s0t1u2
Revises: o6p7q8r9s0t1
Create Date: 2026-08-21
"""

from alembic import op
import sqlalchemy as sa


revision = "p7q8r9s0t1u2"
down_revision = "o6p7q8r9s0t1"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "patient_facesheet",
        sa.Column("primary_payer_type", sa.String(), nullable=True),
    )
    op.add_column(
        "patient_facesheet",
        sa.Column("secondary_payer_type", sa.String(), nullable=True),
    )


def downgrade():
    op.drop_column("patient_facesheet", "secondary_payer_type")
    op.drop_column("patient_facesheet", "primary_payer_type")
