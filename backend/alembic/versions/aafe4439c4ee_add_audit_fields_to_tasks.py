"""add audit fields to tasks

Revision ID: aafe4439c4ee
Revises: 50a4ef7d9c9d
Create Date: 2026-04-30 08:17:32.555755

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aafe4439c4ee'
down_revision: Union[str, Sequence[str], None] = '50a4ef7d9c9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
