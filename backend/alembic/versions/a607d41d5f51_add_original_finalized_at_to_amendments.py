"""add original_finalized_at to amendments

Revision ID: a607d41d5f51
Revises: 0a657b8a9c6b
Create Date: 2026-05-02 07:51:36.897889

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a607d41d5f51'
down_revision: Union[str, Sequence[str], None] = '0a657b8a9c6b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "amendments",
        sa.Column("original_finalized_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("amendments", "original_finalized_at")