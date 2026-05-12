"""add_summary_and_poc_action_to_idg_reviews

Revision ID: 13d23132e68c
Revises: 343bbcfaebc3
Create Date: 2026-05-07 16:29:24.053751

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '13d23132e68c'
down_revision: Union[str, Sequence[str], None] = '343bbcfaebc3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # These columns exist in the SQLAlchemy model but are missing in the DB table.
    # Nullable=True is intentional (safe for existing rows).
    op.add_column("idg_reviews", sa.Column("summary", sa.Text(), nullable=True))
    op.add_column("idg_reviews", sa.Column("poc_action", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("idg_reviews", "poc_action")
    op.drop_column("idg_reviews", "summary")