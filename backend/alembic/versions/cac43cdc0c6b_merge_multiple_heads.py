"""merge_multiple_heads

Revision ID: cac43cdc0c6b
Revises: 19ab16ca90c1, 7b4d161eb9af
Create Date: 2026-05-05 20:22:36.210592

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cac43cdc0c6b'
down_revision: Union[str, Sequence[str], None] = ('19ab16ca90c1', '7b4d161eb9af')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
