"""activate love and faith billing

Revision ID: b8f3c1d5e4aa
Revises: 7d9e4a1c2b3f
Create Date: 2026-08-13 23:40:00.000000
"""

from __future__ import annotations

from alembic import op


revision = "b8f3c1d5e4aa"
down_revision = "7d9e4a1c2b3f"
branch_labels = None
depends_on = None


TENANT_ID = "01271980-0000-0000-0000-000005101977"


def upgrade() -> None:
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS ai_enabled BOOLEAN NOT NULL DEFAULT false;")
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS billing_enabled BOOLEAN NOT NULL DEFAULT false;")
    op.execute(
        f"""
        UPDATE tenants
        SET display_name = 'Love & Faith Hospice Services Inc.',
            ai_enabled = true,
            billing_enabled = true
        WHERE id = '{TENANT_ID}'::uuid
        """
    )


def downgrade() -> None:
    op.execute(
        f"""
        UPDATE tenants
        SET display_name = 'Sunrise Hospice Care',
            ai_enabled = false,
            billing_enabled = false
        WHERE id = '{TENANT_ID}'::uuid
        """
    )
