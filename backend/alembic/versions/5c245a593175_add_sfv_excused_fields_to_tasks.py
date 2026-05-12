"""add sfv excused fields to tasks

Revision ID: 5c245a593175
Revises: 8f2b1249a9a8
Create Date: 2026-05-05 08:22:16.800299

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c245a593175'
down_revision: Union[str, Sequence[str], None] = '8f2b1249a9a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column("tasks", sa.Column("excused_reason_code", sa.String(length=64), nullable=True))
    op.add_column("tasks", sa.Column("excused_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tasks", sa.Column("excused_source", sa.String(length=32), nullable=True))

def downgrade():
    op.drop_column("tasks", "excused_source")
    op.drop_column("tasks", "excused_at")
    op.drop_column("tasks", "excused_reason_code")