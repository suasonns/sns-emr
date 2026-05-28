"""repair_create_foundation_tables_dev_clean

Revision ID: de6941fcac1d
Revises: 0f431da522aa
Create Date: 2026-05-27 18:50:14.947242

Forward-only repair migration.

Creates foundational tables in sns_emr_dev_clean if missing:
- public.tenants
- public.roles
- public.interfaces

This migration is defensive and survey-safe.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "de6941fcac1d"
down_revision: Union[str, Sequence[str], None] = "0f431da522aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(bind, table_name: str) -> bool:
    return sa.inspect(bind).has_table(table_name, schema="public")


def upgrade() -> None:
    bind = op.get_bind()

    # -------------------------------------------------
    # tenants
    # -------------------------------------------------
    if not _has_table(bind, "tenants"):
        op.create_table(
            "tenants",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                nullable=False,
            ),
            sa.Column(
                "name",
                sa.String(length=200),
                nullable=False,
                server_default=sa.text("'DEV'"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=False),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=False),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "created_by",
                postgresql.UUID(as_uuid=True),
                nullable=True,
            ),
            schema="public",
        )

    # -------------------------------------------------
    # roles
    # -------------------------------------------------
    if not _has_table(bind, "roles"):
        op.create_table(
            "roles",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                nullable=False,
            ),
            sa.Column(
                "name",
                sa.String(length=100),
                nullable=False,
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=False),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            schema="public",
        )
        op.create_index(
            "ix_roles_name",
            "roles",
            ["name"],
            unique=True,
            schema="public",
        )

    # -------------------------------------------------
    # interfaces
    # -------------------------------------------------
    if not _has_table(bind, "interfaces"):
        op.create_table(
            "interfaces",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                nullable=False,
            ),
            sa.Column(
                "name",
                sa.String(length=120),
                nullable=False,
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=False),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            schema="public",
        )
        op.create_index(
            "ix_interfaces_name",
            "interfaces",
            ["name"],
            unique=True,
            schema="public",
        )


def downgrade() -> None:
    # Forward-only repair migration — no downgrade
    pass