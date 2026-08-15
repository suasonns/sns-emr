# =========================================================
# FILE: alembic/versions/<generated_revision_id>_validate_poc_fks.py
# PURPOSE: Repair orphan plan_of_care row, then validate FKs
# SAFE SCOPE:
#   - delete one known orphan plan_of_care row
#   - validate fk_plan_of_care_patient_id_patients
#   - validate fk_plan_of_care_tenant_id_tenants
#
# NOTE:
#   - This migration is intentionally manual and forward-only.
#   - It targets the single orphan row already identified in the DB.
# =========================================================

"""validate_poc_fks

Revision ID: f7581fb279ce
Revises: 4662185002bd
Create Date: 2026-07-19 11:56:41.111757

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7581fb279ce'
down_revision: Union[str, Sequence[str], None] = '4662185002bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -----------------------------------------------------
    # 1) Delete the one known orphan plan_of_care row
    # -----------------------------------------------------
    op.execute(
        """
        DELETE FROM plan_of_care
        WHERE id = '32e5089f-2429-467b-b830-ebf7ea041c1f'
          AND patient_id = '6dcead44-7c5e-4c78-bde6-1ded8954b983'
          AND tenant_id = '01271980-0000-0000-0000-000005101977'
          AND admission_id IS NULL;
        """
    )

    # -----------------------------------------------------
    # 2) Safety check: fail if any patient orphans still exist
    # -----------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM plan_of_care poc
                LEFT JOIN patients p
                  ON p.id = poc.patient_id
                WHERE p.id IS NULL
            ) THEN
                RAISE EXCEPTION
                    'Cannot validate fk_plan_of_care_patient_id_patients: orphan patient references still exist in plan_of_care';
            END IF;
        END
        $$;
        """
    )

    # -----------------------------------------------------
    # 3) Safety check: fail if any tenant orphans still exist
    # -----------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM plan_of_care poc
                LEFT JOIN tenants t
                  ON t.id = poc.tenant_id
                WHERE t.id IS NULL
            ) THEN
                RAISE EXCEPTION
                    'Cannot validate fk_plan_of_care_tenant_id_tenants: orphan tenant references still exist in plan_of_care';
            END IF;
        END
        $$;
        """
    )

    # -----------------------------------------------------
    # 4) Validate patient FK if present and not yet validated
    # -----------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_plan_of_care_patient_id_patients'
                  AND convalidated = false
            ) THEN
                ALTER TABLE plan_of_care
                VALIDATE CONSTRAINT fk_plan_of_care_patient_id_patients;
            END IF;
        END
        $$;
        """
    )

    # -----------------------------------------------------
    # 5) Validate tenant FK if present and not yet validated
    # -----------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_plan_of_care_tenant_id_tenants'
                  AND convalidated = false
            ) THEN
                ALTER TABLE plan_of_care
                VALIDATE CONSTRAINT fk_plan_of_care_tenant_id_tenants;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    # -----------------------------------------------------
    # Forward-only migration
    # The orphan row deletion is intentionally not recreated.
    # Constraint validation is also not reversed.
    # -----------------------------------------------------
    pass