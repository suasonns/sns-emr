"""add IDG_REVIEW to tasks_task_type_enum

Revision ID: d8e10b78f236
Revises: f58020cc5ea2
Create Date: 2026-xx-xx xx:xx:xx.xxxxxx
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d8e10b78f236"
down_revision: Union[str, Sequence[str], None] = "f58020cc5ea2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add 'IDG_REVIEW' to tasks_task_type_enum.

    Enterprise-safe implementation:
    - Avoids op.get_context().autocommit_block() (can assert in some Alembic contexts)
    - Ends any active transaction before switching to AUTOCOMMIT (SQLAlchemy 2.x)
    """
    conn = op.get_bind()

    # End any active transaction before switching isolation level.
    try:
        if hasattr(conn, "in_transaction") and conn.in_transaction():
            conn.commit()
    except Exception:
        pass

    ac = conn.execution_options(isolation_level="AUTOCOMMIT")
    ac.execute(
        sa.text(
            "ALTER TYPE tasks_task_type_enum "
            "ADD VALUE IF NOT EXISTS 'IDG_REVIEW'"
        )
    )


def downgrade() -> None:
    # PostgreSQL enums are forward-only.
    pass
