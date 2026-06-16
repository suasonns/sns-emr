"""repair audit_logs add description and metadata fields

Revision ID: bf6f447fbe5e
Revises: c91e027a25c1
Create Date: 2026-06-04 12:07:53.503381
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "bf6f447fbe5e"
down_revision: Union[str, Sequence[str], None] = "c91e027a25c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Repair migration:
    Align audit_logs table with AuditLog model and audit_logger payload.
    Adds columns only if they do not already exist.
    """
    bind = op.get_bind()

    def col_exists(column_name: str) -> bool:
        return bind.execute(
            sa.text(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'audit_logs'
                  AND column_name = :column_name
                LIMIT 1
                """
            ),
            {"column_name": column_name},
        ).scalar() is not None

    # Context fields
    if not col_exists("request_id"):
        op.add_column(
            "audit_logs",
            sa.Column("request_id", sa.UUID(), nullable=True),
        )

    if not col_exists("ip_address"):
        op.add_column(
            "audit_logs",
            sa.Column("ip_address", sa.String(length=64), nullable=True),
        )

    # Narrative / description
    if not col_exists("description"):
        op.add_column(
            "audit_logs",
            sa.Column("description", sa.Text(), nullable=True),
        )

    # Structured metadata
    if not col_exists("metadata"):
        op.add_column(
            "audit_logs",
            sa.Column(
                "metadata",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
        )


def downgrade() -> None:
    """
    Best-effort downgrade for dev/test only.
    """
    bind = op.get_bind()

    def col_exists(column_name: str) -> bool:
        return bind.execute(
            sa.text(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'audit_logs'
                  AND column_name = :column_name
                LIMIT 1
                """
            ),
            {"column_name": column_name},
        ).scalar() is not None

    if col_exists("metadata"):
        op.drop_column("audit_logs", "metadata")
    if col_exists("description"):
        op.drop_column("audit_logs", "description")
    if col_exists("ip_address"):
        op.drop_column("audit_logs", "ip_address")
    if col_exists("request_id"):
        op.drop_column("audit_logs", "request_id")
