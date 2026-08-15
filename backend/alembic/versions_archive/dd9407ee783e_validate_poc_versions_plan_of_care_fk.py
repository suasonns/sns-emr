# =========================================================
# FILE: alembic/versions/<generated_revision_id>_validate_poc_versions_plan_of_care_fk.py
# PURPOSE: Validate FK plan_of_care_versions.plan_of_care_id -> plan_of_care.id
# =========================================================

"""validate_poc_versions_plan_of_care_fk

Revision ID: dd9407ee783e
Revises: 044699079871
Create Date: 2026-07-19 12:20:19.058179

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd9407ee783e'
down_revision: Union[str, Sequence[str], None] = '044699079871'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # -----------------------------------------------------
    # Safety check: fail if any orphan version rows still exist
    # -----------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM plan_of_care_versions pv
                LEFT JOIN plan_of_care poc
                  ON poc.id = pv.plan_of_care_id
                WHERE poc.id IS NULL
            ) THEN
                RAISE EXCEPTION
                    'Cannot validate fk_pocv_plan_of_care_id_plan_of_care: orphan plan_of_care_id references still exist in plan_of_care_versions';
            END IF;
        END
        $$;
        """
    )

    # -----------------------------------------------------
    # Validate FK if present and not yet validated
    # -----------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_pocv_plan_of_care_id_plan_of_care'
                  AND convalidated = false
            ) THEN
                ALTER TABLE plan_of_care_versions
                VALIDATE CONSTRAINT fk_pocv_plan_of_care_id_plan_of_care;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    # Forward-only validation migration
    pass