"""repair add incident_id to tasks

Revision ID: c91e027a25c1
Revises: 1ae2664b2f5f
Create Date: 2026-06-04 11:50:19.321663
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c91e027a25c1"
down_revision: Union[str, Sequence[str], None] = "1ae2664b2f5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Repair migration:
    Add tasks.incident_id (nullable UUID).

    Foreign key intentionally omitted until incident_reports
    metadata registration is verified.
    """
    op.add_column(
        "tasks",
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade reverses the repair by dropping tasks.incident_id."""
    op.drop_column("tasks", "incident_id")