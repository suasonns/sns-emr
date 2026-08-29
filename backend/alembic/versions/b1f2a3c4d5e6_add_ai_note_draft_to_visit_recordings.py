"""add ai_note_draft to visit_recordings

Revision ID: b1f2a3c4d5e6
Revises: a0eef84ab626
Create Date: 2026-08-29 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b1f2a3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'a0eef84ab626'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "visit_recordings",
        sa.Column(
            "ai_note_draft",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("visit_recordings", "ai_note_draft")
