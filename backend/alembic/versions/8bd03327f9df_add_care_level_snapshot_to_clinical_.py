"""add care_level_snapshot to clinical_notes

Revision ID: 8bd03327f9df
Revises: 8f4075cb8649
Create Date: 2026-07-17 18:51:51.026258

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8bd03327f9df'
down_revision: Union[str, Sequence[str], None] = '8f4075cb8649'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "clinical_notes",
        sa.Column("care_level_snapshot", sa.String(length=20), nullable=True),
    )

def downgrade():
    op.drop_column("clinical_notes", "care_level_snapshot")
