"""Merge benefit periods branch with main branch

Revision ID: d0524c53226e
Revises: b677e343f59f, e0a21abe5e4e
Create Date: 2026-05-11 17:22:36.365542

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd0524c53226e'
down_revision: Union[str, Sequence[str], None] = ('b677e343f59f', 'e0a21abe5e4e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
