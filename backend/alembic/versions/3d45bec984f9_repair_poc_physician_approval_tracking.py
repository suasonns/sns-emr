"""repair poc physician approval tracking

Revision ID: 3d45bec984f9
Revises: 3c460d203249
Create Date: 2026-07-07 10:46:55.467330

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3d45bec984f9"
down_revision: Union[str, Sequence[str], None] = "3c460d203249"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    print(">>> RUNNING 3d45bec984f9 UPGRADE <<<")

    op.execute("SELECT 1")
    """
    Repair migration.

    The POC approval tables, constraints, and indexes
    were already created and verified in PostgreSQL.

    This migration records the verified schema state
    into Alembic history.
    """

    op.execute("SELECT 1")


def downgrade() -> None:
    raise RuntimeError(
        "Downgrade disabled. Use forward-only repair migrations."
    )