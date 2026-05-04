"""add drug_aliases table

Revision ID: 28f85a8cd21f
Revises: c6eb02e21077
Create Date: 2026-05-03 10:14:17.485667

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '28f85a8cd21f'
down_revision: Union[str, Sequence[str], None] = 'c6eb02e21077'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
