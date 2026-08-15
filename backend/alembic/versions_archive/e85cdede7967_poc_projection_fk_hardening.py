# =========================================================
# FILE: alembic/versions/<generated_revision_id>_poc_projection_fk_hardening.py
# PURPOSE: Manual forward-only FK hardening for POC projection tables
#
# TABLES:
#   - poc_problems
#   - poc_goals
#   - poc_interventions
#
# SAFE SCOPE:
#   Add missing FKs as NOT VALID only
#   (no validation in this migration)
#
# WHY:
#   Current DB screenshots show only PRIMARY KEY on these tables.
#   Tenant orphan checks are currently 0 rows, but parent/user FK orphan
#   checks have not yet been verified, so validation is deferred.
# =========================================================

"""poc_projection_fk_hardening

Revision ID: e85cdede7967
Revises: dd9407ee783e
Create Date: 2026-07-19 12:29:53.694952

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e85cdede7967'
down_revision: Union[str, Sequence[str], None] = 'dd9407ee783e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -----------------------------------------------------
    # poc_problems
    # -----------------------------------------------------

    # tenant_id -> tenants.id
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_poc_problems_tenant_id_tenants'
            ) THEN
                ALTER TABLE poc_problems
                ADD CONSTRAINT fk_poc_problems_tenant_id_tenants
                FOREIGN KEY (tenant_id)
                REFERENCES tenants(id)
                ON DELETE CASCADE
                NOT VALID;
            END IF;
        END
        $$;
        """
    )

    # poc_version_id -> plan_of_care_versions.id
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_poc_problems_poc_version_id_poc_versions'
            ) THEN
                ALTER TABLE poc_problems
                ADD CONSTRAINT fk_poc_problems_poc_version_id_poc_versions
                FOREIGN KEY (poc_version_id)
                REFERENCES plan_of_care_versions(id)
                ON DELETE CASCADE
                NOT VALID;
            END IF;
        END
        $$;
        """
    )

    # created_by_user_id -> users.id
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_poc_problems_created_by_user_id_users'
            ) THEN
                ALTER TABLE poc_problems
                ADD CONSTRAINT fk_poc_problems_created_by_user_id_users
                FOREIGN KEY (created_by_user_id)
                REFERENCES users(id)
                ON DELETE SET NULL
                NOT VALID;
            END IF;
        END
        $$;
        """
    )

    # updated_by_user_id -> users.id
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_poc_problems_updated_by_user_id_users'
            ) THEN
                ALTER TABLE poc_problems
                ADD CONSTRAINT fk_poc_problems_updated_by_user_id_users
                FOREIGN KEY (updated_by_user_id)
                REFERENCES users(id)
                ON DELETE SET NULL
                NOT VALID;
            END IF;
        END
        $$;
        """
    )

    # -----------------------------------------------------
    # poc_goals
    # -----------------------------------------------------

    # tenant_id -> tenants.id
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_poc_goals_tenant_id_tenants'
            ) THEN
                ALTER TABLE poc_goals
                ADD CONSTRAINT fk_poc_goals_tenant_id_tenants
                FOREIGN KEY (tenant_id)
                REFERENCES tenants(id)
                ON DELETE CASCADE
                NOT VALID;
            END IF;
        END
        $$;
        """
    )

    # poc_problem_id -> poc_problems.id
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_poc_goals_poc_problem_id_poc_problems'
            ) THEN
                ALTER TABLE poc_goals
                ADD CONSTRAINT fk_poc_goals_poc_problem_id_poc_problems
                FOREIGN KEY (poc_problem_id)
                REFERENCES poc_problems(id)
                ON DELETE CASCADE
                NOT VALID;
            END IF;
        END
        $$;
        """
    )

    # created_by_user_id -> users.id
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_poc_goals_created_by_user_id_users'
            ) THEN
                ALTER TABLE poc_goals
                ADD CONSTRAINT fk_poc_goals_created_by_user_id_users
                FOREIGN KEY (created_by_user_id)
                REFERENCES users(id)
                ON DELETE SET NULL
                NOT VALID;
            END IF;
        END
        $$;
        """
    )

    # updated_by_user_id -> users.id
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_poc_goals_updated_by_user_id_users'
            ) THEN
                ALTER TABLE poc_goals
                ADD CONSTRAINT fk_poc_goals_updated_by_user_id_users
                FOREIGN KEY (updated_by_user_id)
                REFERENCES users(id)
                ON DELETE SET NULL
                NOT VALID;
            END IF;
        END
        $$;
        """
    )

    # -----------------------------------------------------
    # poc_interventions
    # -----------------------------------------------------

    # tenant_id -> tenants.id
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_poc_interventions_tenant_id_tenants'
            ) THEN
                ALTER TABLE poc_interventions
                ADD CONSTRAINT fk_poc_interventions_tenant_id_tenants
                FOREIGN KEY (tenant_id)
                REFERENCES tenants(id)
                ON DELETE CASCADE
                NOT VALID;
            END IF;
        END
        $$;
        """
    )

    # poc_goal_id -> poc_goals.id
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_poc_interventions_poc_goal_id_poc_goals'
            ) THEN
                ALTER TABLE poc_interventions
                ADD CONSTRAINT fk_poc_interventions_poc_goal_id_poc_goals
                FOREIGN KEY (poc_goal_id)
                REFERENCES poc_goals(id)
                ON DELETE CASCADE
                NOT VALID;
            END IF;
        END
        $$;
        """
    )

    # created_by_user_id -> users.id
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_poc_interventions_created_by_user_id_users'
            ) THEN
                ALTER TABLE poc_interventions
                ADD CONSTRAINT fk_poc_interventions_created_by_user_id_users
                FOREIGN KEY (created_by_user_id)
                REFERENCES users(id)
                ON DELETE SET NULL
                NOT VALID;
            END IF;
        END
        $$;
        """
    )

    # updated_by_user_id -> users.id
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_poc_interventions_updated_by_user_id_users'
            ) THEN
                ALTER TABLE poc_interventions
                ADD CONSTRAINT fk_poc_interventions_updated_by_user_id_users
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
    # poc_interventions
    # -----------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_poc_interventions_updated_by_user_id_users'
            ) THEN
                ALTER TABLE poc_interventions
                DROP CONSTRAINT fk_poc_interventions_updated_by_user_id_users;
            END IF;
        END
        $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_poc_interventions_created_by_user_id_users'
            ) THEN
                ALTER TABLE poc_interventions
                DROP CONSTRAINT fk_poc_interventions_created_by_user_id_users;
            END IF;
        END
        $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_poc_interventions_poc_goal_id_poc_goals'
            ) THEN
                ALTER TABLE poc_interventions
                DROP CONSTRAINT fk_poc_interventions_poc_goal_id_poc_goals;
            END IF;
        END
        $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_poc_interventions_tenant_id_tenants'
            ) THEN
                ALTER TABLE poc_interventions
                DROP CONSTRAINT fk_poc_interventions_tenant_id_tenants;
            END IF;
        END
        $$;
        """
    )

    # -----------------------------------------------------
    # poc_goals
    # -----------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_poc_goals_updated_by_user_id_users'
            ) THEN
                ALTER TABLE poc_goals
                DROP CONSTRAINT fk_poc_goals_updated_by_user_id_users;
            END IF;
        END
        $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_poc_goals_created_by_user_id_users'
            ) THEN
                ALTER TABLE poc_goals
                DROP CONSTRAINT fk_poc_goals_created_by_user_id_users;
            END IF;
        END
        $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_poc_goals_poc_problem_id_poc_problems'
            ) THEN
                ALTER TABLE poc_goals
                DROP CONSTRAINT fk_poc_goals_poc_problem_id_poc_problems;
            END IF;
        END
        $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_poc_goals_tenant_id_tenants'
            ) THEN
                ALTER TABLE poc_goals
                DROP CONSTRAINT fk_poc_goals_tenant_id_tenants;
            END IF;
        END
        $$;
        """
    )

    # -----------------------------------------------------
    # poc_problems
    # -----------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_poc_problems_updated_by_user_id_users'
            ) THEN
                ALTER TABLE poc_problems
                DROP CONSTRAINT fk_poc_problems_updated_by_user_id_users;
            END IF;
        END
        $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_poc_problems_created_by_user_id_users'
            ) THEN
                ALTER TABLE poc_problems
                DROP CONSTRAINT fk_poc_problems_created_by_user_id_users;
            END IF;
        END
        $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_poc_problems_poc_version_id_poc_versions'
            ) THEN
                ALTER TABLE poc_problems
                DROP CONSTRAINT fk_poc_problems_poc_version_id_poc_versions;
            END IF;
        END
        $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_poc_problems_tenant_id_tenants'
            ) THEN
                ALTER TABLE poc_problems
                DROP CONSTRAINT fk_poc_problems_tenant_id_tenants;
            END IF;
        END
        $$;
        """
    )
