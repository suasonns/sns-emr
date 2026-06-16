"""
add display_name to tenants

Revision ID: 6f7963234886
Revises: a43a968a9b6d
Create Date: 2026-06-03 13:48:29.567017
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# ----------------------------------------------------------------------
# Alembic revision identifiers
# ----------------------------------------------------------------------

revision: str = "6f7963234886"
down_revision: Union[str, Sequence[str], None] = "a43a968a9b6d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ----------------------------------------------------------------------
# Upgrade
# ----------------------------------------------------------------------

def upgrade() -> None:
    """
    Adds display_name to core.tenants if it does not already exist.
    Idempotent repair migration.
    """

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    columns = [col["name"] for col in inspector.get_columns("tenants", schema="core")]

    if "display_name" not in columns:
        op.add_column(
            "tenants",
            sa.Column("display_name", sa.Text(), nullable=True),
            schema="core",
        )

# ----------------------------------------------------------------------
# Downgrade
# ----------------------------------------------------------------------

def downgrade() -> None:
    """
    Downgrade intentionally blocked.

    Removing display_name would break dashboards and audit views.
    """
    raise RuntimeError(
        "Downgrade not permitted for add display_name to tenants migration"
    )