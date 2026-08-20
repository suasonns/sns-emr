"""add cosignature_due_at to physician_orders

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-19 10:20:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "physician_orders",
        sa.Column("cosignature_due_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade():
    op.drop_column("physician_orders", "cosignature_due_at")
