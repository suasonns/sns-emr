"""merge rnica and form engine heads

Revision ID: a8ec3016df7b
Revises: ('0b73f1e255db', '76dca1229fdf')
Create Date: 2026-08-13 02:15:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a8ec3016df7b"
down_revision: Union[str, Sequence[str], None] = ("0b73f1e255db", "76dca1229fdf")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
