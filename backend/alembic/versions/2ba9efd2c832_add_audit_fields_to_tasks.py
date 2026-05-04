"""add audit fields to tasks

Revision ID: 2ba9efd2c832
Revises: aafe4439c4ee
Create Date: 2026-04-30 08:18:58.570022
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = "2ba9efd2c832"
down_revision: Union[str, Sequence[str], None] = "aafe4439c4ee"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "tasks",
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.add_column(
        "tasks",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.add_column(
        "tasks",
        sa.Column(
            "created_by",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_tasks_created_by",
        "tasks",
        ["created_by"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_tasks_created_by", table_name="tasks")
    op.drop_column("tasks", "created_by")
    op.drop_column("tasks", "updated_at")
    op.drop_column("tasks", "created_at")
