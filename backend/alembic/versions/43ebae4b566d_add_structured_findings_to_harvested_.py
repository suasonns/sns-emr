"""add structured findings to harvested signals

Revision ID: 43ebae4b566d
Revises: f3a7c9d2b4e1
Create Date: 2026-08-27 11:35:47.860518

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '43ebae4b566d'
down_revision: Union[str, Sequence[str], None] = 'f3a7c9d2b4e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "patient_harvested_signals",
        sa.Column(
            "structured_findings",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("patient_harvested_signals", "structured_findings")
