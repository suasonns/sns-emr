"""add field_provenance to rnica_assessments

Revision ID: a0eef84ab626
Revises: 9c2d4e6f8a1b
Create Date: 2026-08-28 16:14:59.349856

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a0eef84ab626'
down_revision: Union[str, Sequence[str], None] = '9c2d4e6f8a1b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "rnica_assessments",
        sa.Column(
            "field_provenance",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("rnica_assessments", "field_provenance")
