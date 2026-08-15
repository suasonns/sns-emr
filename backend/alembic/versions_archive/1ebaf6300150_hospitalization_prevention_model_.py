"""hospitalization_prevention_model_registration_marker

Revision ID: 1ebaf6300150
Revises: 1d5baf814a70
Create Date: 2026-08-04 17:18:46.189290

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1ebaf6300150'
down_revision: Union[str, Sequence[str], None] = '1d5baf814a70'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
