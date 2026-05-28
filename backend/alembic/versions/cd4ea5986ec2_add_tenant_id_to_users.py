"""add_tenant_id_to_users

Revision ID: cd4ea5986ec2
Revises: f5ee8cb51e19
Create Date: 2026-05-27 19:12:25.987293

Forward-only migration.

Adds tenant_id to users table.
Required for multi-tenant authentication and dev-login upsert.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# ------------------------------------------------------------------
# Alembic identifiers
# ------------------------------------------------------------------
revision = "cd4ea5986ec2"
down_revision = "f5ee8cb51e19"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add tenant_id column
    op.add_column(
        "users",
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        schema="public",
    )

    # Index for tenant-scoped queries
    op.create_index(
        "ix_users_tenant_id",
        "users",
        ["tenant_id"],
        schema="public",
    )

    # Foreign key to tenants (safe, nullable, survey-defensible)
    op.create_foreign_key(
        "fk_users_tenant_id",
        "users",
        "tenants",
        ["tenant_id"],
        ["id"],
        source_schema="public",
        referent_schema="public",
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # Forward-only migration
    pass