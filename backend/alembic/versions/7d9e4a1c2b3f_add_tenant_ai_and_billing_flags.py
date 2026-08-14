"""add tenant ai and billing flags

Revision ID: 7d9e4a1c2b3f
Revises: 9d1ab3f2c7e4
Create Date: 2026-08-13 22:10:00.000000
"""

from __future__ import annotations

from alembic import op


revision = "7d9e4a1c2b3f"
down_revision = "9d1ab3f2c7e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS ai_enabled BOOLEAN NOT NULL DEFAULT false;")
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS billing_enabled BOOLEAN NOT NULL DEFAULT false;")


def downgrade() -> None:
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS billing_enabled;")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS ai_enabled;")
