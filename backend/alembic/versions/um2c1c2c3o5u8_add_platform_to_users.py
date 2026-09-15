"""add platform assignment to users

Revision ID: um2c1c2c3o5u8
Revises: um2b1c2c3o5u7
Create Date: 2026-09-14 00:00:00.000000

Drift correction: the SNS Staff & Access organizational hierarchy must
be Platform > Department > Job Title > Platform Role > Access Level --
Department was previously the highest organizational assignment level,
which does not scale once additional SNS platforms (SNS Home Health
Solutions, SNS Scribe) exist. This adds `platform` as a first-class,
backend-persisted column, defaulting every existing and new account to
"SNS Hospice Solutions" (the only currently-staffed platform). See
app/core/platforms.py for the canonical allowed-values list.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'um2c1c2c3o5u8'
down_revision: Union[str, Sequence[str], None] = 'um2b1c2c3o5u7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "platform",
            sa.String(length=120),
            nullable=False,
            server_default="SNS Hospice Solutions",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "platform")
