"""add visits.visit_discipline

Revision ID: 1b65d1470563
Revises: 288d8809a335
Create Date: 2026-05-29 10:13:30.405413

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1b65d1470563'
down_revision: Union[str, Sequence[str], None] = '288d8809a335'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "visits",
        sa.Column("visit_discipline", sa.String(length=32), nullable=True),
    )


def downgrade():
    op.drop_column("visits", "visit_discipline")