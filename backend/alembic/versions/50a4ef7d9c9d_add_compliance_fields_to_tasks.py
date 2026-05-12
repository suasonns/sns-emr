"""Add compliance fields to tasks

Revision ID: 50a4ef7d9c9d
Revises: 4c586d69e593
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "50a4ef7d9c9d"
down_revision = "4c586d69e593"
branch_labels = None
depends_on = None


def _create_enum_if_not_exists(enum_name: str, values: list[str]) -> None:
    """
    Safely create a PostgreSQL ENUM type only if it doesn't already exist.
    """
    # Build quoted enum labels: 'A','B','C'
    labels = ", ".join([f"'{v}'" for v in values])

    op.execute(f"""
    DO $$
    BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{enum_name}') THEN
        EXECUTE 'CREATE TYPE {enum_name} AS ENUM ({labels})';
      END IF;
    END $$;
    """)


def upgrade() -> None:
    # Ensure the tasks table exists
    op.execute("""
    DO $$
    BEGIN
      IF to_regclass('public.tasks') IS NULL THEN
        RAISE EXCEPTION 'public.tasks does not exist; tasks creator migration was not applied';
      END IF;
    END $$;
    """)

    # Create enums safely (no dynamic EXECUTE needed)
    op.execute("""
    DO $$
    BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tasks_task_type_enum') THEN
        CREATE TYPE tasks_task_type_enum AS ENUM ('HUV', 'SFV', 'OTHER');
      END IF;

      IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tasks_origin_enum') THEN
        CREATE TYPE tasks_origin_enum AS ENUM ('ADMISSION', 'PERIODIC', 'MANUAL');
      END IF;

      IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tasks_discipline_enum') THEN
        CREATE TYPE tasks_discipline_enum AS ENUM ('RN', 'MD', 'NP', 'SW', 'CHAPLAIN', 'AIDE');
      END IF;

      IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tasks_status_enum') THEN
        CREATE TYPE tasks_status_enum AS ENUM ('PENDING', 'COMPLETED', 'OVERDUE', 'ESCALATED', 'WAIVED');
      END IF;

      IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tasks_completion_ref_enum') THEN
        CREATE TYPE tasks_completion_ref_enum AS ENUM ('VISIT', 'NOTE', 'ORDER');
      END IF;

      IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tasks_regulatory_basis_enum') THEN
        CREATE TYPE tasks_regulatory_basis_enum AS ENUM ('IDG', 'VISIT_FREQUENCY', 'F2F', 'CERTIFICATION', 'ADMISSION_REQUIREMENT');
      END IF;
    END $$;
    """)

    # Add columns safely (idempotent) — schema-qualified
    op.execute("""
    ALTER TABLE public.tasks
      ADD COLUMN IF NOT EXISTS task_type tasks_task_type_enum;

    ALTER TABLE public.tasks
      ADD COLUMN IF NOT EXISTS origin tasks_origin_enum;

    ALTER TABLE public.tasks
      ADD COLUMN IF NOT EXISTS discipline tasks_discipline_enum;

    ALTER TABLE public.tasks
      ADD COLUMN IF NOT EXISTS regulatory_basis tasks_regulatory_basis_enum;

    ALTER TABLE public.tasks
      ADD COLUMN IF NOT EXISTS due_date DATE;

    ALTER TABLE public.tasks
      ADD COLUMN IF NOT EXISTS status tasks_status_enum;

    ALTER TABLE public.tasks
      ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITHOUT TIME ZONE;

    ALTER TABLE public.tasks
      ADD COLUMN IF NOT EXISTS completion_reference_type tasks_completion_ref_enum;

    ALTER TABLE public.tasks
      ADD COLUMN IF NOT EXISTS completion_reference_id VARCHAR;

    ALTER TABLE public.tasks
      ADD COLUMN IF NOT EXISTS assigned_user_id UUID;

    ALTER TABLE public.tasks
      ADD COLUMN IF NOT EXISTS benefit_period_id UUID;
    """)

def downgrade() -> None:
    # Leave downgrade minimal/safe for dev: do not drop columns/enums (avoid destructive rollback)
    pass