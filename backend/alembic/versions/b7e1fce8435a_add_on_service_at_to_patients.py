"""add on_service_at to patients

Revision ID: b7e1fce8435a
Revises: 33247aa788ef
Create Date: 2026-06-01 16:42:15.360095
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision: str = "b7e1fce8435a"
down_revision: Union[str, Sequence[str], None] = "33247aa788ef"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Verify that patients.on_service_at exists.

    This migration is verification-only because the column
    has already been created by the table owner / DBA.
    """
    conn = op.get_bind()

    result = conn.execute(
        text(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'patients'
              AND column_name = 'on_service_at';
            """
        )
    ).fetchone()

    if result is None:
        raise RuntimeError(
            "Expected column patients.on_service_at does not exist. "
            "Schema is behind expected revision b7e1fce8435a."
        )


def downgrade() -> None:
    """
    No-op downgrade.

    Column removal is intentionally not automated
    for audit and safety reasons.
    """
    pass