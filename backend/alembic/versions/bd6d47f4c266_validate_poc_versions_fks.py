# =========================================================
# FILE: alembic/versions/<generated_revision_id>_validate_poc_versions_fks.py
# PURPOSE: Repair orphan plan_of_care_versions row, then validate FKs
# SAFE SCOPE:
#   - delete one known orphan plan_of_care_versions row
#   - validate fk_pocv_tenant_id_tenants
#   - validate fk_pocv_created_by_user_id_users
#   - validate fk_pocv_updated_by_user_id_users
#
# NOTE:
#   - This is a forward-only manual repair migration.
#   - The orphan row has no parent plan_of_care row, so backfill is not possible.
# =========================================================

"""validate_poc_versions_fks

Revision ID: bd6d47f4c266
Revises: 469c10d17a14
Create Date: 2026-07-19 12:10:20.966821

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bd6d47f4c266'
down_revision: Union[str, Sequence[str], None] = '469c10d17a14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -----------------------------------------------------
    # 1) Delete the one known orphan version row
    # -----------------------------------------------------
    op.execute(
        """
        DELETE FROM plan_of_care_versions
        WHERE id = 'f35e7ddf-baa3-4899-b5a7-2d7ba1722442'
          AND plan_of_care_id = '32e5089f-2429-467b-b830-ebf7ea041c1f'
          AND tenant_id IS NULL
          AND version_number = 1;
        """
    )

    # -----------------------------------------------------
    # 2) Safety check: fail if any tenant orphans still exist
    # -----------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM plan_of_care_versions pv
                LEFT JOIN tenants t
                  ON t.id = pv.tenant_id
                WHERE t.id IS NULL
            ) THEN
                RAISE EXCEPTION
                    'Cannot validate fk_pocv_tenant_id_tenants: orphan tenant references still exist in plan_of_care_versions';
            END IF;
        END
        $$;
        """
    )

    # -----------------------------------------------------
    # 3) Safety check: fail if any created_by_user_id orphans exist
    # -----------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM plan_of_care_versions pv
                LEFT JOIN users u
                  ON u.id = pv.created_by_user_id
                WHERE pv.created_by_user_id IS NOT NULL
                  AND u.id IS NULL
            ) THEN
                RAISE EXCEPTION
                    'Cannot validate fk_pocv_created_by_user_id_users: orphan created_by_user_id references still exist in plan_of_care_versions';
            END IF;
        END
        $$;
        """
    )

    # -----------------------------------------------------
    # 4) Safety check: fail if any updated_by_user_id orphans exist
    # -----------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM plan_of_care_versions pv
                LEFT JOIN users u
                  ON u.id = pv.updated_by_user_id
                WHERE pv.updated_by_user_id IS NOT NULL
                  AND u.id IS NULL
            ) THEN
                RAISE EXCEPTION
                    'Cannot validate fk_pocv_updated_by_user_id_users: orphan updated_by_user_id references still exist in plan_of_care_versions';
            END IF;
        END
        $$;
        """
    )

    # -----------------------------------------------------
    # 5) Validate tenant FK
    # -----------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_pocv_tenant_id_tenants'
                  AND convalidated = false
            ) THEN
                ALTER TABLE plan_of_care_versions
                VALIDATE CONSTRAINT fk_pocv_tenant_id_tenants;
            END IF;
        END
        $$;
        """
    )

    # -----------------------------------------------------
    # 6) Validate created_by FK
    # -----------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_pocv_created_by_user_id_users'
                  AND convalidated = false
            ) THEN
                ALTER TABLE plan_of_care_versions
                VALIDATE CONSTRAINT fk_pocv_created_by_user_id_users;
            END IF;
        END
        $$;
        """
    )

    # -----------------------------------------------------
    # 7) Validate updated_by FK
    # -----------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_pocv_updated_by_user_id_users'
                  AND convalidated = false
            ) THEN
                ALTER TABLE plan_of_care_versions
                VALIDATE CONSTRAINT fk_pocv_updated_by_user_id_users;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    # Forward-only repair migration
    pass