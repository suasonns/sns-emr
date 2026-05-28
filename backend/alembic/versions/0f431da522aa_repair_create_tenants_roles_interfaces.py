"""repair_create_tenants_roles_interfaces

Revision ID: 0f431da522aa
Revises: 533c2ae752e8
Create Date: 2026-05-27 18:14:12.461198
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0f431da522aa"
down_revision: Union[str, Sequence[str], None] = "533c2ae752e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(bind, table_name: str) -> bool:
    insp = sa.inspect(bind)
    return insp.has_table(table_name, schema="public")


def upgrade() -> None:
    """
    Forward-only repair migration.

    Creates foundational multi-tenant tables if missing:
    - public.tenants
    - public.roles
    - public.interfaces

    This is defensive because the environment is stamped at head but missing tables.
    """
    bind = op.get_bind()

    # ----------------------------
    # tenants
    # ----------------------------
    if not _has_table(bind, "tenants"):
        op.create_table(
            "tenants",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False, server_default=sa.text("'DEV'")),
            sa.Column("created_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.text("now()")),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
            schema="public",
        )
        op.create_index("ix_tenants_created_by", "tenants", ["created_by"], schema="public")

        # Create FK only if users table exists (defensive)
        if _has_table(bind, "users"):
            op.create_foreign_key(
                "fk_tenants_created_by_users",
                "tenants",
                "users",
                ["created_by"],
                ["id"],
                source_schema="public",
                referent_schema="public",
                ondelete=None,
            )

    # ----------------------------
    # roles
    # ----------------------------
    if not _has_table(bind, "roles"):
        op.create_table(
            "roles",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.text("now()")),
            schema="public",
        )
        op.create_index("ix_roles_name", "roles", ["name"], unique=True, schema="public")

    # ----------------------------
    # interfaces
    # ----------------------------
    if not _has_table(bind, "interfaces"):
        op.create_table(
            "interfaces",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.text("now()")),
            schema="public",
        )
        op.create_index("ix_interfaces_name", "interfaces", ["name"], unique=True, schema="public")


def downgrade() -> None:
    """
    Forward-only policy: no downgrade for repair migrations.
    """
    pass