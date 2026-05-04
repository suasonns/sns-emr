"""merge idg repair heads

Revision ID: 73ad350a8be4
Revises: 96889fea4832, df5449917920
Create Date: 2026-05-02 15:59:04.677436

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '73ad350a8be4'
down_revision: Union[str, Sequence[str], None] = ('96889fea4832', 'df5449917920')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
