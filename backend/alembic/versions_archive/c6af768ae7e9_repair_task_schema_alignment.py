"""
repair_task_schema_alignment

Revision ID: c6af768ae7e9
Revises: 7d8e12be82ec
Create Date: 2026-08-13 02:40:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c6af768ae7e9"
down_revision: Union[str, Sequence[str], None] = "7d8e12be82ec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("priority", sa.String(), nullable=True))
    op.add_column("tasks", sa.Column("clinical_severity", sa.String(), nullable=True))
    op.add_column("tasks", sa.Column("assigned_role", sa.String(), nullable=True))
    op.add_column(
        "tasks",
        sa.Column("notification_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column("tasks", sa.Column("reference_type", sa.String(), nullable=True))
    op.add_column("tasks", sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=True))

    op.execute(sa.text("ALTER TABLE tasks ALTER COLUMN regulatory_basis DROP NOT NULL;"))
    op.execute(sa.text("ALTER TABLE tasks ALTER COLUMN due_date DROP NOT NULL;"))


def downgrade() -> None:
    op.execute(sa.text("ALTER TABLE tasks ALTER COLUMN regulatory_basis SET NOT NULL;"))
    op.execute(sa.text("ALTER TABLE tasks ALTER COLUMN due_date SET NOT NULL;"))

    op.drop_column("tasks", "reference_id")
    op.drop_column("tasks", "reference_type")
    op.drop_column("tasks", "notification_required")
    op.drop_column("tasks", "assigned_role")
    op.drop_column("tasks", "clinical_severity")
    op.drop_column("tasks", "priority")
