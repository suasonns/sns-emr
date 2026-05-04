"""add hospice_election_date to patients

Revision ID: 3dec96845e87
Revises: d8e10b78f236
Create Date: 2026-05-01 05:52:06.293785

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3dec96845e87'
down_revision: Union[str, Sequence[str], None] = 'd8e10b78f236'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "patients",
        sa.Column("hospice_election_date", sa.Date(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
