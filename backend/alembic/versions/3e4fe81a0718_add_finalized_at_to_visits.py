"""add finalized_at to visits

Revision ID: 3e4fe81a0718
Revises: 1f74a6ffb06f
Create Date: 2026-05-01 16:34:21.416811
"""

from alembic import op
import sqlalchemy as sa

# ✅ REQUIRED Alembic identifiers
revision = "3e4fe81a0718"
down_revision = "1f74a6ffb06f"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "visits",
        sa.Column("finalized_at", sa.DateTime(timezone=False), nullable=True),
    )


def downgrade():
    op.drop_column("visits", "finalized_at")