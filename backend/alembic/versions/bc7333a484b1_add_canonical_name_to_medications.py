"""add canonical_name to medications

Revision ID: bc7333a484b1
Revises: e7aaf711f77b
Create Date: 2026-05-03 12:49:14.513562

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bc7333a484b1'
down_revision: Union[str, Sequence[str], None] = 'e7aaf711f77b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "medications",
        sa.Column("canonical_name", sa.String(length=255), nullable=True)
    )
    op.create_index(
        "ix_medications_canonical_name",
        "medications",
        ["canonical_name"],
    )

def downgrade():
    op.drop_index("ix_medications_canonical_name", table_name="medications")
    op.drop_column("medications", "canonical_name")
