"""add visit_mode to visits

Revision ID: 122debb94552
Revises: 1b65d1470563
Create Date: 2026-05-29 12:10:56.554901

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '122debb94552'
down_revision: Union[str, Sequence[str], None] = '1b65d1470563'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "visits",
        sa.Column("visit_mode", sa.String(), nullable=False, server_default="IN_PERSON"),
    )
    # Optional: remove server_default after backfill so inserts must specify or app default applies
    op.alter_column("visits", "visit_mode", server_default=None)

def downgrade():
    op.drop_column("visits", "visit_mode")
