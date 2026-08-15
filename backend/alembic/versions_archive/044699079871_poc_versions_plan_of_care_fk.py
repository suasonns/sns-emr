# =========================================================
# FILE: alembic/versions/044699079871_poc_versions_plan_of_care_fk.py
# PURPOSE: Add FK plan_of_care_versions.plan_of_care_id → plan_of_care.id
# STATUS: SAFE (NOT VALID FIRST)
# =========================================================

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "044699079871"
down_revision = "bd6d47f4c266"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -----------------------------------------------------
    # Add FK (NOT VALID first to avoid breaking existing data)
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
                  AND c.conname = 'fk_pocv_plan_of_care_id_plan_of_care'
            ) THEN
                ALTER TABLE plan_of_care_versions
                ADD CONSTRAINT fk_pocv_plan_of_care_id_plan_of_care
                FOREIGN KEY (plan_of_care_id)
                REFERENCES plan_of_care(id)
                ON DELETE CASCADE
                NOT VALID;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_pocv_plan_of_care_id_plan_of_care'
            ) THEN
                ALTER TABLE plan_of_care_versions
                DROP CONSTRAINT fk_pocv_plan_of_care_id_plan_of_care;
            END IF;
        END
        $$;
        """
    )