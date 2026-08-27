"""add ecog_score_previous/current to f2f_encounters

Revision ID: y1a2b3c4d5e6
Revises: x8y9z0a1b2c3
Create Date: 2026-08-23 21:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "y1a2b3c4d5e6"
down_revision = "x8y9z0a1b2c3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "f2f_encounters",
        sa.Column("ecog_score_previous", sa.Integer(), nullable=True),
    )
    op.add_column(
        "f2f_encounters",
        sa.Column("ecog_score_current", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("f2f_encounters", "ecog_score_current")
    op.drop_column("f2f_encounters", "ecog_score_previous")
