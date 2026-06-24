"""add access_level to users

Revision ID: 230ca950caa5
Revises: 52be2c0a3eaa
Create Date: 2026-06-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = "230ca950caa5"
down_revision: Union[str, Sequence[str], None] = "52be2c0a3eaa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =====================================================
    # ADD COLUMN: access_level
    # =====================================================
    op.add_column(
        "users",
        sa.Column(
            "access_level",
            sa.String(length=32),
            nullable=False,
            server_default="ROLE_BASED"
        )
    )

    # =====================================================
    # OPTIONAL: REMOVE DEFAULT (clean production state)
    # =====================================================
    op.alter_column(
        "users",
        "access_level",
        server_default=None
    )


def downgrade() -> None:
    # =====================================================
    # REMOVE COLUMN
    # =====================================================
    op.drop_column("users", "access_level")