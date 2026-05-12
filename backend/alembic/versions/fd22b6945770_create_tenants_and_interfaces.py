"""create tenants and interfaces

Revision ID: fd22b6945770
Revises: c1989b77d090
Create Date: 2026-05-07 09:22:18.115041

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fd22b6945770'
down_revision: Union[str, Sequence[str], None] = 'c1989b77d090'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # -------------------------------------------------------------
    # Tenants: legal isolation boundary (HIPAA-critical)
    # -------------------------------------------------------------
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("legal_name", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="ACTIVE"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # -------------------------------------------------------------
    # Interfaces: permission context boundaries
    # -------------------------------------------------------------
    op.create_table(
        "interfaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade():
    # NOTE: Downgrade included for completeness.
    # In practice, enterprise systems do not downgrade prod.
    op.drop_table("interfaces")
    op.drop_table("tenants")