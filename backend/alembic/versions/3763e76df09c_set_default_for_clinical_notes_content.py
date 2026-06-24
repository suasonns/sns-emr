"""set default for clinical_notes.content

Revision ID: 3763e76df09c
Revises: 2f227d63cf1f
Create Date: 2026-06-23 14:42:26.340263

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3763e76df09c'
down_revision: Union[str, Sequence[str], None] = '2f227d63cf1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column(
        "clinical_notes",
        "content",
        existing_type=sa.Text(),
        nullable=False,
        server_default=sa.text("''"),
    )


def downgrade():
    op.alter_column(
        "clinical_notes",
        "content",
        existing_type=sa.Text(),
        nullable=False,
        server_default=None,
    )