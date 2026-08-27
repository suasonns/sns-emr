"""add tenant cbsa_code

Revision ID: a49295a82a41
Revises: f4a6d1e8b3c7
Create Date: 2026-08-24

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a49295a82a41"
down_revision = "f4a6d1e8b3c7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column("cbsa_code", sa.String(length=10), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tenants", "cbsa_code")
