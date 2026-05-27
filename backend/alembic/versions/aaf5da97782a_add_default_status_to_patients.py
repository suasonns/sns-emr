"""add default status to patients

Revision ID: aaf5da97782a
Revises: 81d8dfcde545
Create Date: 2026-05-26 16:14:10.959022

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aaf5da97782a'
down_revision: Union[str, Sequence[str], None] = '81d8dfcde545'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Set DB-level default
    op.alter_column(
        "patients",
        "status",
        server_default=sa.text("'ACTIVE'"),
        existing_nullable=False,
    )


def downgrade():
    op.alter_column(
        "patients",
        "status",
        server_default=None,
        existing_nullable=False,
    )
