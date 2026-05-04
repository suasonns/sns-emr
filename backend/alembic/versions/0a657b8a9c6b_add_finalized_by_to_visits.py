"""add finalized_by to visits

Revision ID: 0a657b8a9c6b
Revises: 7d1ae9d7f91e
Create Date: 2026-05-02 07:30:09.144593
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "0a657b8a9c6b"
down_revision = "7d1ae9d7f91e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "visits",
        sa.Column("finalized_by", UUID(as_uuid=True), nullable=True),
    )


def downgrade():
    op.drop_column("visits", "finalized_by")