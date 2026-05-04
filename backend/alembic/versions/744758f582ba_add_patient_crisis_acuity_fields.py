"""add patient crisis acuity fields

Revision ID: 744758f582ba
Revises: 095a7ebe661a
Create Date: 2026-04-30 14:51:17.953835

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '744758f582ba'
down_revision: Union[str, Sequence[str], None] = '095a7ebe661a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("patients", sa.Column("acuity_state", sa.String(), nullable=False, server_default="ROUTINE"))
    op.add_column("patients", sa.Column("crisis_started_at", sa.DateTime(), nullable=True))
    op.add_column("patients", sa.Column("crisis_ended_at", sa.DateTime(), nullable=True))

def downgrade() -> None:
    op.drop_column("patients", "crisis_ended_at")
    op.drop_column("patients", "crisis_started_at")
    op.drop_column("patients", "acuity_state")
