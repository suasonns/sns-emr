"""Create tasks table (minimal)

Revision ID: 4c586d69e593
Revises: 3a88b97a921b
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "4c586d69e593"
down_revision = "3a88b97a921b"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tasks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String, nullable=False),
    )


def downgrade():
    op.drop_table("tasks")