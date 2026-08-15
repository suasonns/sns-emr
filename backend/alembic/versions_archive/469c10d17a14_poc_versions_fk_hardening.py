# =========================================================
# FILE: alembic/versions/<generated_revision_id>_poc_versions_fk_hardening.py
# PURPOSE: Manual forward-only FK hardening for plan_of_care_versions
# SAFE SCOPE:
#   - add FK: tenant_id -> tenants.id (NOT VALID)
#   - add FK: created_by_user_id -> users.id (NOT VALID)
#   - add FK: updated_by_user_id -> users.id (NOT VALID)
#
# IMPORTANT:
# - This migration intentionally DOES NOT validate the new foreign keys.
# - Existing orphan rows (if any) must be cleaned first in a later repair migration.
# - This keeps the stabilization change small and safe.
# =========================================================

"""poc_versions_fk_hardening

Revision ID: 469c10d17a14
Revises: f7581fb279ce
Create Date: 2026-07-19 12:04:32.379500

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '469c10d17a14'
down_revision: Union[str, Sequence[str], None] = 'f7581fb279ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -----------------------------------------------------
    # 1) FK: tenant_id -> tenants.id
    # -----------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint c
                JOIN pg_class t
                  ON t.oid = c.conrelid
                WHERE c.contype = 'f'
                  AND t.relname = 'plan_of_care_versions'
                  AND c.conname = 'fk_pocv_tenant_id_tenants'
            ) THEN
                ALTER TABLE plan_of_care_versions
                ADD CONSTRAINT fk_pocv_tenant_id_tenants
                FOREIGN KEY (tenant_id)
                REFERENCES tenants(id)
                ON DELETE CASCADE
                NOT VALID;
            END IF;
        END
        $$;
        """
    )

    # -----------------------------------------------------
    # 2) FK: created_by_user_id -> users.id
    # -----------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint c
                JOIN pg_class t
                  ON t.oid = c.conrelid
                WHERE c.contype = 'f'
                  AND t.relname = 'plan_of_care_versions'
                  AND c.conname = 'fk_pocv_created_by_user_id_users'
            ) THEN
                ALTER TABLE plan_of_care_versions
                ADD CONSTRAINT fk_pocv_created_by_user_id_users
                FOREIGN KEY (created_by_user_id)
                REFERENCES users(id)
                ON DELETE SET NULL
                NOT VALID;
            END IF;
        END
        $$;
        """
    )

    # -----------------------------------------------------
    # 3) FK: updated_by_user_id -> users.id
    # -----------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint c
                JOIN pg_class t
                  ON t.oid = c.conrelid
                WHERE c.contype = 'f'
                  AND t.relname = 'plan_of_care_versions'
                  AND c.conname = 'fk_pocv_updated_by_user_id_users'
            ) THEN
                ALTER TABLE plan_of_care_versions
                ADD CONSTRAINT fk_pocv_updated_by_user_id_users
                FOREIGN KEY (updated_by_user_id)
                REFERENCES users(id)
                ON DELETE SET NULL
                NOT VALID;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    # -----------------------------------------------------
    # Drop FK: updated_by_user_id -> users.id
    # -----------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_pocv_updated_by_user_id_users'
            ) THEN
                ALTER TABLE plan_of_care_versions
                DROP CONSTRAINT fk_pocv_updated_by_user_id_users;
            END IF;
        END
        $$;
        """
    )

    # -----------------------------------------------------
    # Drop FK: created_by_user_id -> users.id
    # -----------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_pocv_created_by_user_id_users'
            ) THEN
                ALTER TABLE plan_of_care_versions
                DROP CONSTRAINT fk_pocv_created_by_user_id_users;
            END IF;
        END
        $$;
        """
    )

    # -----------------------------------------------------
    # Drop FK: tenant_id -> tenants.id
    # -----------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_pocv_tenant_id_tenants'
            ) THEN
                ALTER TABLE plan_of_care_versions
                DROP CONSTRAINT fk_pocv_tenant_id_tenants;
            END IF;
        END
        $$;
        """
    )