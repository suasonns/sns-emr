"""repair add clinical_note_id to tasks

Revision ID: 1ae2664b2f5f
Revises: fe1386604aff
Create Date: 2026-06-04 11:43:35.932467
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "1ae2664b2f5f"
down_revision: Union[str, Sequence[str], None] = "fe1386604aff"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Repair migration:
    Add tasks.clinical_note_id (nullable UUID).

    FK intentionally omitted until table name is confirmed (clinical_notes vs clinical_note, etc.).
    Forward-only: do not rewrite history.
    """
    op.add_column(
        "tasks",
        sa.Column("clinical_note_id", postgresql.UUID(as_uuid=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade reverses the repair by dropping tasks.clinical_note_id."""
    op.drop_column("tasks", "clinical_note_id")
