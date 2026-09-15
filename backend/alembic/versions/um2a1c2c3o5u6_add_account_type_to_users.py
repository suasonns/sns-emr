"""add account_type to users

Revision ID: um2a1c2c3o5u6
Revises: um2s1a2f3f4b5
Create Date: 2026-09-05 00:00:00.000000

Phase UM-2A. Adds users.account_type (HUMAN_STAFF / SERVICE_ACCOUNT /
AUTOMATION_ACCOUNT / API_CLIENT -- see app/core/account_types.py),
defaulting every existing row to HUMAN_STAFF since all current platform
and tenant staff rows are human accounts.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'um2a1c2c3o5u6'
down_revision: Union[str, Sequence[str], None] = 'um2s1a2f3f4b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "account_type",
            sa.String(length=32),
            nullable=False,
            server_default="HUMAN_STAFF",
        ),
    )
    op.create_check_constraint(
        "ck_users_account_type_valid",
        "users",
        "account_type IN ('HUMAN_STAFF', 'SERVICE_ACCOUNT', 'AUTOMATION_ACCOUNT', 'API_CLIENT')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_account_type_valid", "users", type_="check")
    op.drop_column("users", "account_type")
