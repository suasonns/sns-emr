"""add completed_at to tasks

Revision ID: 924041973331
Revises: 2ba9efd2c832
Create Date: 2026-04-30 12:25:38.257749
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "924041973331"
down_revision: Union[str, Sequence[str], None] = "2ba9efd2c832"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tasks", "completed_at")