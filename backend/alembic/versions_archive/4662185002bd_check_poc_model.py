# =========================================================
# FILE: alembic/versions/4662185002bd_check_poc_model.py
# PURPOSE: Manual forward-only hardening for plan_of_care
# SAFE SCOPE:
#   - add composite index: ix_poc_tenant_admission
#   - add FK: plan_of_care.patient_id -> patients.id (NOT VALID)
#   - add FK: plan_of_care.tenant_id -> tenants.id (NOT VALID)
#
# IMPORTANT:
# - This migration intentionally DOES NOT validate the new foreign keys.
# - Existing orphan rows currently prevent validation.
# - NOT VALID allows the constraint to exist without checking old bad rows.
# - A later repair migration can validate after data cleanup.
# =========================================================

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "4662185002bd"
down_revision = "8bd03327f9df"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -----------------------------------------------------
    # 1) Composite index for tenant + admission lookup
    # -----------------------------------------------------
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_poc_tenant_admission
        ON plan_of_care (tenant_id, admission_id);
        """
    )

    # -----------------------------------------------------
    # 2) FK: patient_id -> patients.id
    # Add as NOT VALID so existing orphan rows do not block migration
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
                  AND t.relname = 'plan_of_care'
                  AND c.conname = 'fk_plan_of_care_patient_id_patients'
            ) THEN
                ALTER TABLE plan_of_care
                ADD CONSTRAINT fk_plan_of_care_patient_id_patients
                FOREIGN KEY (patient_id)
                REFERENCES patients(id)
                ON DELETE CASCADE
                NOT VALID;
            END IF;
        END
        $$;
        """
    )

    # -----------------------------------------------------
    # 3) FK: tenant_id -> tenants.id
    # Add as NOT VALID so existing orphan rows do not block migration
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
                  AND t.relname = 'plan_of_care'
                  AND c.conname = 'fk_plan_of_care_tenant_id_tenants'
            ) THEN
                ALTER TABLE plan_of_care
                ADD CONSTRAINT fk_plan_of_care_tenant_id_tenants
                FOREIGN KEY (tenant_id)
                REFERENCES tenants(id)
                ON DELETE CASCADE
                NOT VALID;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    # -----------------------------------------------------
    # Drop FK: patient_id -> patients.id
    # -----------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_plan_of_care_patient_id_patients'
            ) THEN
                ALTER TABLE plan_of_care
                DROP CONSTRAINT fk_plan_of_care_patient_id_patients;
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
                WHERE conname = 'fk_plan_of_care_tenant_id_tenants'
            ) THEN
                ALTER TABLE plan_of_care
                DROP CONSTRAINT fk_plan_of_care_tenant_id_tenants;
            END IF;
        END
        $$;
        """
    )

    # -----------------------------------------------------
    # Drop composite index
    # -----------------------------------------------------
    op.execute(
        """
        DROP INDEX IF EXISTS ix_poc_tenant_admission;
        """
    )