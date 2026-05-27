"""repair tasks add discipline regulatory_basis alert_reason created_by

Revision ID: a0bb66070697
Revises: 9825899d568a
Create Date: 2026-05-26 19:35:41.868065

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a0bb66070697'
down_revision: Union[str, Sequence[str], None] = '9825899d568a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Add missing columns expected by SQLAlchemy Task model (nullable = backward compatible)
    op.add_column("tasks", sa.Column("discipline", sa.String(length=16), nullable=True))
    op.add_column("tasks", sa.Column("regulatory_basis", sa.String(length=64), nullable=True))
    op.add_column("tasks", sa.Column("alert_reason", sa.String(length=255), nullable=True))
    op.add_column("tasks", sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True))

    # Optional: indexes for common reporting/filters (safe to include)
    op.create_index("ix_tasks_discipline", "tasks", ["discipline"], unique=False)
    op.create_index("ix_tasks_regulatory_basis", "tasks", ["regulatory_basis"], unique=False)


def downgrade():
    op.drop_index("ix_tasks_regulatory_basis", table_name="tasks")
    op.drop_index("ix_tasks_discipline", table_name="tasks")

    op.drop_column("tasks", "created_by")
    op.drop_column("tasks", "alert_reason")
    op.drop_column("tasks", "regulatory_basis")
    op.drop_column("tasks", "discipline")