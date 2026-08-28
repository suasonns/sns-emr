"""add client_request_id to rnica_assessments for offline-sync idempotency

Revision ID: 9c2d4e6f8a1b
Revises: 7b1f2c9a0d34
Create Date: 2026-08-28 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "9c2d4e6f8a1b"
down_revision = "7b1f2c9a0d34"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "rnica_assessments",
        sa.Column("client_request_id", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_rnica_assessments_client_request_id",
        "rnica_assessments",
        ["client_request_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_rnica_assessments_client_request_id", table_name="rnica_assessments")
    op.drop_column("rnica_assessments", "client_request_id")
