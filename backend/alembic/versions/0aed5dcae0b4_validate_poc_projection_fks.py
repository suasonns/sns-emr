# =========================================================
# FILE: alembic/versions/<generated_revision_id>_validate_poc_projection_fks.py
# PURPOSE: Validate FK constraints for POC projection tables
#
# TABLES:
#   - poc_problems
#   - poc_goals
#   - poc_interventions
#
# SAFETY:
#   - verifies ZERO orphan rows exist before validation
#   - only then validates NOT VALID constraints
#
# NOTE:
#   This is forward-only and will fail safely if data issues exist
# =========================================================

"""validate_poc_projection_fks

Revision ID: 0aed5dcae0b4
Revises: e85cdede7967
Create Date: 2026-07-19 12:42:25.113439

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0aed5dcae0b4'
down_revision: Union[str, Sequence[str], None] = 'e85cdede7967'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =====================================================
    # SAFETY CHECKS (FAIL FAST IF ANY ORPHANS EXIST)
    # =====================================================

    op.execute(
        """
        DO $$
        BEGIN
            -- poc_problems -> plan_of_care_versions
            IF EXISTS (
                SELECT 1
                FROM poc_problems p
                LEFT JOIN plan_of_care_versions v
                  ON v.id = p.poc_version_id
                WHERE v.id IS NULL
            ) THEN
                RAISE EXCEPTION
                'Cannot validate poc_problems FK: orphan poc_version_id exists';
            END IF;

            -- poc_goals -> poc_problems
            IF EXISTS (
                SELECT 1
                FROM poc_goals g
                LEFT JOIN poc_problems p
                  ON p.id = g.poc_problem_id
                WHERE p.id IS NULL
            ) THEN
                RAISE EXCEPTION
                'Cannot validate poc_goals FK: orphan poc_problem_id exists';
            END IF;

            -- poc_interventions -> poc_goals
            IF EXISTS (
                SELECT 1
                FROM poc_interventions i
                LEFT JOIN poc_goals g
                  ON g.id = i.poc_goal_id
                WHERE g.id IS NULL
            ) THEN
                RAISE EXCEPTION
                'Cannot validate poc_interventions FK: orphan poc_goal_id exists';
            END IF;

            -- users FK checks (created_by)
            IF EXISTS (
                SELECT 1 FROM poc_problems p
                LEFT JOIN users u ON u.id = p.created_by_user_id
                WHERE p.created_by_user_id IS NOT NULL AND u.id IS NULL
            ) THEN
                RAISE EXCEPTION 'poc_problems created_by orphan detected';
            END IF;

            IF EXISTS (
                SELECT 1 FROM poc_goals g
                LEFT JOIN users u ON u.id = g.created_by_user_id
                WHERE g.created_by_user_id IS NOT NULL AND u.id IS NULL
            ) THEN
                RAISE EXCEPTION 'poc_goals created_by orphan detected';
            END IF;

            IF EXISTS (
                SELECT 1 FROM poc_interventions i
                LEFT JOIN users u ON u.id = i.created_by_user_id
                WHERE i.created_by_user_id IS NOT NULL AND u.id IS NULL
            ) THEN
                RAISE EXCEPTION 'poc_interventions created_by orphan detected';
            END IF;

            -- users FK checks (updated_by)
            IF EXISTS (
                SELECT 1 FROM poc_problems p
                LEFT JOIN users u ON u.id = p.updated_by_user_id
                WHERE p.updated_by_user_id IS NOT NULL AND u.id IS NULL
            ) THEN
                RAISE EXCEPTION 'poc_problems updated_by orphan detected';
            END IF;

            IF EXISTS (
                SELECT 1 FROM poc_goals g
                LEFT JOIN users u ON u.id = g.updated_by_user_id
                WHERE g.updated_by_user_id IS NOT NULL AND u.id IS NULL
            ) THEN
                RAISE EXCEPTION 'poc_goals updated_by orphan detected';
            END IF;

            IF EXISTS (
                SELECT 1 FROM poc_interventions i
                LEFT JOIN users u ON u.id = i.updated_by_user_id
                WHERE i.updated_by_user_id IS NOT NULL AND u.id IS NULL
            ) THEN
                RAISE EXCEPTION 'poc_interventions updated_by orphan detected';
            END IF;

        END
        $$;
        """
    )

    # =====================================================
    # VALIDATE CONSTRAINTS
    # =====================================================

    op.execute(
        """
        DO $$
        BEGIN

            -- ===============================
            -- poc_problems
            -- ===============================
            ALTER TABLE poc_problems VALIDATE CONSTRAINT fk_poc_problems_tenant_id_tenants;
            ALTER TABLE poc_problems VALIDATE CONSTRAINT fk_poc_problems_poc_version_id_poc_versions;
            ALTER TABLE poc_problems VALIDATE CONSTRAINT fk_poc_problems_created_by_user_id_users;
            ALTER TABLE poc_problems VALIDATE CONSTRAINT fk_poc_problems_updated_by_user_id_users;

            -- ===============================
            -- poc_goals
            -- ===============================
            ALTER TABLE poc_goals VALIDATE CONSTRAINT fk_poc_goals_tenant_id_tenants;
            ALTER TABLE poc_goals VALIDATE CONSTRAINT fk_poc_goals_poc_problem_id_poc_problems;
            ALTER TABLE poc_goals VALIDATE CONSTRAINT fk_poc_goals_created_by_user_id_users;
            ALTER TABLE poc_goals VALIDATE CONSTRAINT fk_poc_goals_updated_by_user_id_users;

            -- ===============================
            -- poc_interventions
            -- ===============================
            ALTER TABLE poc_interventions VALIDATE CONSTRAINT fk_poc_interventions_tenant_id_tenants;
            ALTER TABLE poc_interventions VALIDATE CONSTRAINT fk_poc_interventions_poc_goal_id_poc_goals;
            ALTER TABLE poc_interventions VALIDATE CONSTRAINT fk_poc_interventions_created_by_user_id_users;
            ALTER TABLE poc_interventions VALIDATE CONSTRAINT fk_poc_interventions_updated_by_user_id_users;

        END
        $$;
        """
    )


def downgrade() -> None:
    # forward-only validation migration
    pass