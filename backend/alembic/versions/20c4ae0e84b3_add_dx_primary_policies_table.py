"""add_dx_primary_policies_table

Revision ID: 20c4ae0e84b3
Revises: a62ad7d643fd
Create Date: 2026-05-20 19:10:49.387778

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20c4ae0e84b3'
down_revision: Union[str, Sequence[str], None] = 'a62ad7d643fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dx_primary_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("diagnosis_code", sa.String(length=64), nullable=False),
        sa.Column("diagnosis_name", sa.String(length=255), nullable=False),
        sa.Column("allowed_primary", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("rationale", sa.String(length=512), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_index(
        "ix_dx_primary_policies_code",
        "dx_primary_policies",
        ["diagnosis_code"],
        unique=True,
    )


def downgrade() -> None:
    pass