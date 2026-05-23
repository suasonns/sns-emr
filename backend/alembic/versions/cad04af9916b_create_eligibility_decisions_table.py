"""create eligibility_decisions table

Revision ID: cad04af9916b
Revises: 2d5531b3965b
Create Date: 2026-05-22 14:29:47.584833

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cad04af9916b'
down_revision: Union[str, Sequence[str], None] = '2d5531b3965b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "eligibility_decisions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("patient_id", sa.Integer, nullable=False),

        sa.Column("decision", sa.String(length=50), nullable=False),

        sa.Column("lcd_id", sa.String(length=20), nullable=False),
        sa.Column("mac", sa.String(length=20), nullable=False),
        sa.Column("mac_type", sa.String(length=10), nullable=False),
        sa.Column("lcd_effective_date", sa.Date, nullable=False),

        sa.Column("decision_timestamp", sa.DateTime, nullable=False),
        sa.Column("config_hash", sa.String(length=64), nullable=False),
    )


def downgrade():
    op.drop_table("eligibility_decisions")