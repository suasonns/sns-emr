"""add_finalized_at_to_idg_reviews

Revision ID: 3a4f0af44d73
Revises: 8aabf0c30144
Create Date: 2026-05-04 10:02:50.579279
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '3a4f0af44d73'
down_revision: Union[str, Sequence[str], None] = '8aabf0c30144'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "idg_reviews",
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade():
    pass
