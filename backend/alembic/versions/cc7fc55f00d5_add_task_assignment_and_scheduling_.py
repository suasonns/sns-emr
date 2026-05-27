"""add task assignment and scheduling fields

Revision ID: cc7fc55f00d5
Revises: 3b236f1a012b
Create Date: 2026-05-26 16:45:24.097071

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'cc7fc55f00d5'
down_revision: Union[str, Sequence[str], None] = '3b236f1a012b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade():
    op.add_column("tasks", sa.Column("assigned_user_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("tasks", sa.Column("scheduled_start_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tasks", sa.Column("schedule_status", sa.String(length=24), nullable=False, server_default=sa.text("'NEEDS_SCHEDULING'")))

    op.create_index("ix_tasks_assigned_user", "tasks", ["assigned_user_id"])
    op.create_index("ix_tasks_schedule_status", "tasks", ["schedule_status"])


def downgrade():
    op.drop_index("ix_tasks_schedule_status", table_name="tasks")
    op.drop_index("ix_tasks_assigned_user", table_name="tasks")
    op.drop_column("tasks", "schedule_status")
    op.drop_column("tasks", "scheduled_start_at")
    op.drop_column("tasks", "assigned_user_id")