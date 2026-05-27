"""add POC_UPDATE regulatory basis to tasks

Revision ID: 095a7ebe661a
Revises: 9a9cf44f4a36
Create Date: 2026-04-30 14:46:19.895989
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "095a7ebe661a"
down_revision: Union[str, Sequence[str], None] = "9a9cf44f4a36"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add 'POC_UPDATE' to tasks_regulatory_basis_enum.

    Enterprise-safe implementation:
    - SQLAlchemy may already have an open transaction (autobegin).
    - You cannot change isolation_level to AUTOCOMMIT until you COMMIT/ROLLBACK.
    - We commit if needed, then run ALTER TYPE using AUTOCOMMIT.
    """
    conn = op.get_bind()

    # End any active transaction before switching isolation level.
    # (SQLAlchemy 2.x raises InvalidRequestError otherwise.)
    try:
        if hasattr(conn, "in_transaction") and conn.in_transaction():
            conn.commit()
    except Exception:
        # If commit isn't available/needed, ignore safely.
        pass

    ac = conn.execution_options(isolation_level="AUTOCOMMIT")
    ac.execute(
        sa.text(
            "ALTER TYPE tasks_regulatory_basis_enum "
            "ADD VALUE IF NOT EXISTS 'POC_UPDATE'"
        )
    )


def downgrade() -> None:
    # PostgreSQL enums are forward-only (cannot easily remove values).
    pass
