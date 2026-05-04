"""add POC_UPDATE regulatory basis to tasks

Revision ID: 095a7ebe661a
Revises: 9a9cf44f4a36
Create Date: 2026-04-30 14:46:19.895989
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa  # keep if you use it later; safe to keep


# revision identifiers, used by Alembic.
revision: str = "095a7ebe661a"
down_revision: Union[str, Sequence[str], None] = "9a9cf44f4a36"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ✅ Run enum ALTER outside the migration transaction for maximum compatibility
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE tasks_regulatory_basis_enum ADD VALUE IF NOT EXISTS 'POC_UPDATE';")


def downgrade() -> None:
    # Safe no-op; PostgreSQL enums cannot easily remove values.
    pass