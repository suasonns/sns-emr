"""add_tenant_id_to_patients

Revision ID: 60a0912e0f06
Revises: cd4ea5986ec2
Create Date: 2026-05-28 08:42:25.120681

Forward-only migration.

Adds tenant_id to patients for multi-tenant scoping.
Fixes /patients endpoints failing on missing patients.tenant_id.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "60a0912e0f06"
down_revision = "cd4ea5986ec2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add tenant_id column (nullable first to avoid breaking existing rows)
    op.add_column(
        "patients",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="public",
    )

    # Index for tenant-scoped queries
    op.create_index(
        "ix_patients_tenant_id",
        "patients",
        ["tenant_id"],
        schema="public",
    )

    # FK to tenants (nullable + SET NULL keeps it safe)
    op.create_foreign_key(
        "fk_patients_tenant_id",
        "patients",
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