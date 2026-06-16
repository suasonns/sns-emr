"""add_npi_to_tenants

Revision ID: a855eeaabf90
Revises: c31940fd09ff
Create Date: 2026-05-31

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a855eeaabf90"
down_revision: Union[str, Sequence[str], None] = "c31940fd09ff"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    ✅ SAFE / IDEMPOTENT NPI MIGRATION

    Strategy:
    1. Add npi column if missing
    2. Backfill existing NULL rows with placeholder
    3. Enforce NOT NULL
    """

    op.execute("""
    DO $$
    BEGIN
        -- -------------------------------------------------
        -- 1. Add column only if missing
        -- -------------------------------------------------
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'tenants'
              AND column_name = 'npi'
        ) THEN
            ALTER TABLE tenants
            ADD COLUMN npi VARCHAR(10);
        END IF;

        -- -------------------------------------------------
        -- 2. Backfill existing NULL rows with placeholder
        -- -------------------------------------------------
        UPDATE tenants
        SET npi = '0000000000'
        WHERE npi IS NULL;

        -- -------------------------------------------------
        -- 3. Enforce NOT NULL
        -- -------------------------------------------------
        ALTER TABLE tenants
        ALTER COLUMN npi SET NOT NULL;
    END$$;
    """)


def downgrade() -> None:
    """
    ⚠️ Forward-only project, rollback kept for completeness
    """

    op.execute("""
    ALTER TABLE tenants
    DROP COLUMN IF EXISTS npi;
    """)