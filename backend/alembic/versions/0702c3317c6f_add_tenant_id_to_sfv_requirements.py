"""add tenant_id to sfv_requirements

Revision ID: 0702c3317c6f
Revises: 6e90f5e96ae0
Create Date: 2026-06-24 22:48:11.916077

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0702c3317c6f'
down_revision: Union[str, Sequence[str], None] = '6e90f5e96ae0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1) Add column as nullable first so existing rows can be backfilled
    op.add_column(
        "sfv_requirements",
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    # 2) Index for tenant-safe lookups
    op.create_index(
        "ix_sfv_requirements_tenant_id",
        "sfv_requirements",
        ["tenant_id"],
        unique=False,
    )

    # 3) Backfill tenant_id from visits using triggering_visit_id
    op.execute(
        """
        UPDATE sfv_requirements s
        SET tenant_id = v.tenant_id
        FROM visits v
        WHERE s.triggering_visit_id = v.id
        """
    )

    # 4) Enforce NOT NULL after backfill
    op.alter_column(
        "sfv_requirements",
        "tenant_id",
        nullable=False,
    )


def downgrade():
    op.drop_index("ix_sfv_requirements_tenant_id", table_name="sfv_requirements")
    op.drop_column("sfv_requirements", "tenant_id")