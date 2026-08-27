"""merge action center and physician lifecycle branches

Revision ID: e2f558bae7ea
Revises: q8r9s0t1u2v3, v1w2x3y4z5a6
Create Date: 2026-08-22 03:23:43.425575

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2f558bae7ea'
down_revision: Union[str, Sequence[str], None] = ('q8r9s0t1u2v3', 'v1w2x3y4z5a6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
