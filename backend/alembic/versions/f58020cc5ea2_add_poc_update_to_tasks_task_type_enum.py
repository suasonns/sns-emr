"""add POC_UPDATE to tasks_task_type_enum

Revision ID: f58020cc5ea2
Revises: d3cc58c6ab3f
Create Date: 2026-xx-xx xx:xx:xx.xxxxxx
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f58020cc5ea2"
down_revision: Union[str, Sequence[str], None] = "d3cc58c6ab3f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add 'POC_UPDATE' to tasks_task_type_enum.

    Enterprise-safe implementation:
    - Avoids op.get_context().autocommit_block() (can assert in some Alembic contexts)
    - Ends any active transaction before switching to AUTOCOMMIT (SQLAlchemy 2.x safety)
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
            "ADD VALUE IF NOT EXISTS 'POC_UPDATE'"
        )
    )


def downgrade() -> None:
    # PostgreSQL enums are forward-only.
    pass