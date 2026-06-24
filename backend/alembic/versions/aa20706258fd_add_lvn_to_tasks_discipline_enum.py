"""add_lvn_to_tasks_discipline_enum

Revision ID: aa20706258fd
Revises: 6eda4cfebcc0
Create Date: 2026-06-19 15:54:50.808447

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aa20706258fd'
down_revision: Union[str, Sequence[str], None] = '6eda4cfebcc0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE tasks_discipline_enum ADD VALUE IF NOT EXISTS 'LVN';")

def downgrade() -> None:
    pass
