"""Provider Signature Authority Model: capture the actual signer's
provider role/credential and (when an alternate authorized provider —
NP/PA — signs a STAT/URGENT order) the required alternate-signer reason
on physician_orders (additive only).

Revision ID: u0v1w2x3y4z5
Revises: t9u0v1w2x3y4
Create Date: 2026-08-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "u0v1w2x3y4z5"
down_revision: Union[str, Sequence[str], None] = "t9u0v1w2x3y4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "physician_orders",
        sa.Column("signed_by_provider_role", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "physician_orders",
        sa.Column("alternate_signer_reason", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("physician_orders", "alternate_signer_reason")
    op.drop_column("physician_orders", "signed_by_provider_role")
