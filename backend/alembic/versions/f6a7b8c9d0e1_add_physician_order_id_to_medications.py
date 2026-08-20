"""add physician_order_id to medications

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-08-19 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "medications",
        sa.Column("physician_order_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_medications_physician_order_id",
        "medications",
        "physician_orders",
        ["physician_order_id"],
        ["id"],
    )
    op.create_index(
        "ix_medications_physician_order_id",
        "medications",
        ["physician_order_id"],
    )


def downgrade():
    op.drop_index("ix_medications_physician_order_id", table_name="medications")
    op.drop_constraint("fk_medications_physician_order_id", "medications", type_="foreignkey")
    op.drop_column("medications", "physician_order_id")
