"""add visit supervisory flag

Revision ID: d3cc58c6ab3f
Revises: 744758f582ba
Create Date: 2026-04-30 14:56:45.220281

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3cc58c6ab3f'
down_revision: Union[str, Sequence[str], None] = '744758f582ba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    op.add_column(
        "visits",
        sa.Column("is_supervisory", sa.Boolean(), nullable=False, server_default=sa.text("false"))
    )

def downgrade() -> None:
    op.drop_column("visits", "is_supervisory")

