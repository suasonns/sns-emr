"""add_tax_id_and_ptan_to_tenants

Revision ID: f35a48856e72
Revises: a855eeaabf90
Create Date: 2026-05-31

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f35a48856e72"
down_revision: Union[str, Sequence[str], None] = "a855eeaabf90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    ✅ Add tax_id (EIN) and ptan columns safely
    ✅ Idempotent (can run multiple times safely)
    """

    op.execute("""
    DO $$
    BEGIN

        -- ✅ Add tax_id if missing
        IF NOT EXISTS (
            SELECT 1 
            FROM information_schema.columns
            WHERE table_name = 'tenants' 
              AND column_name = 'tax_id'
        ) THEN
            ALTER TABLE tenants ADD COLUMN tax_id VARCHAR(15);
        END IF;

        -- ✅ Add ptan if missing
        IF NOT EXISTS (
            SELECT 1 
            FROM information_schema.columns
            WHERE table_name = 'tenants' 
              AND column_name = 'ptan'
        ) THEN
            ALTER TABLE tenants ADD COLUMN ptan VARCHAR(32);
        END IF;

    END$$;
    """)


def downgrade() -> None:
    """
    ⚠️ Forward-only system, rollback kept for completeness
    """

    op.execute("""
    ALTER TABLE tenants DROP COLUMN IF EXISTS ptan;
    ALTER TABLE tenants DROP COLUMN IF EXISTS tax_id;
    """)