"""merge heads: J2052C ownership fix + reconcile model migration drift

Revision ID: f5f4ba60e332
Revises: y9z0a1b2c3d4, 5f54091b0080
Create Date: 2026-09-24 10:53:33.811958

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f5f4ba60e332'
down_revision: Union[str, Sequence[str], None] = ('y9z0a1b2c3d4', '5f54091b0080')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
