"""repair recreate tasks table

Revision ID: 9a9cf44f4a36
Revises: eb851de9e5e1
Create Date: 2026-04-30 13:48:45.744796
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "9a9cf44f4a36"
down_revision = "eb851de9e5e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Repair-only migration (safety-first):
    - If public.tasks already exists, do nothing.
    - If tasks is missing but prerequisites are missing (patients), fail fast with a clear message.
    - Create required ENUMs only if missing (no dynamic EXECUTE/quoting issues).
    - Recreate tasks table WITHOUT referencing users (users may not exist).
    - Add FK to benefit_periods only if benefit_periods exists.
    """

    bind = op.get_bind()

    # If tasks exists, no-op (normal case when b8699a ran) [1](https://suasonns-my.sharepoint.com/personal/romel_suason_suasonns_org/Documents/Microsoft%20Copilot%20Chat%20Files/b8699a65514c_add_task_engine_for_huv_sfv.py)
    tasks_exists = bind.execute(sa.text("SELECT to_regclass('public.tasks')")).scalar()
    if tasks_exists:
        return

    # Patients must exist; if not, DB is drifted beyond repair here.
    patients_exists = bind.execute(sa.text("SELECT to_regclass('public.patients')")).scalar()
    if not patients_exists:
        raise RuntimeError("public.patients does not exist; reset DB and run alembic upgrade head from scratch")

    # Ensure ENUM types exist (idempotent)
    op.execute("""
    DO $$
    BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tasks_task_type_enum') THEN
        CREATE TYPE tasks_task_type_enum AS ENUM ('HUV', 'SFV', 'OTHER');
      END IF;

      IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tasks_origin_enum') THEN
        CREATE TYPE tasks_origin_enum AS ENUM ('ADMISSION', 'PERIODIC', 'MANUAL');
      END IF;

      -- Keep this aligned with the canonical task engine migration (no LVN here)
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

    # Create tasks table (schema-qualified). Do NOT reference users (may not exist).
    op.execute("""
    CREATE TABLE IF NOT EXISTS public.tasks (
      id UUID PRIMARY KEY,
      patient_id UUID NOT NULL REFERENCES public.patients(id) ON DELETE CASCADE,

      -- benefit period is optional; FK added only if benefit_periods exists
      benefit_period_id UUID NULL,

      task_type tasks_task_type_enum NOT NULL,
      origin tasks_origin_enum NOT NULL DEFAULT 'PERIODIC',
      discipline tasks_discipline_enum NOT NULL,
      regulatory_basis tasks_regulatory_basis_enum NOT NULL DEFAULT 'VISIT_FREQUENCY',

      due_date DATE NOT NULL,

      status tasks_status_enum NOT NULL DEFAULT 'PENDING',

      completed_at TIMESTAMP WITHOUT TIME ZONE NULL,
      completion_reference_type tasks_completion_ref_enum NULL,
      completion_reference_id VARCHAR NULL,

      assigned_user_id UUID NULL,   -- no FK to users here (repair-safe)
      created_by UUID NULL,         -- no FK to users here (repair-safe)

      created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
      updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
    );
    """)

    # Add FK to benefit_periods only if that table exists
    op.execute("""
    DO $$
    BEGIN
      IF to_regclass('public.benefit_periods') IS NOT NULL THEN
        -- Add constraint only if not already present
        IF NOT EXISTS (
          SELECT 1 FROM pg_constraint
          WHERE conname = 'tasks_benefit_period_id_fkey'
        ) THEN
          ALTER TABLE public.tasks
            ADD CONSTRAINT tasks_benefit_period_id_fkey
            FOREIGN KEY (benefit_period_id) REFERENCES public.benefit_periods(id);
        END IF;
      END IF;
    END $$;
    """)

    # Indexes (idempotent)
    op.execute("CREATE INDEX IF NOT EXISTS idx_tasks_patient ON public.tasks(patient_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON public.tasks(due_date);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON public.tasks(status);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_tasks_discipline ON public.tasks(discipline);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_tasks_benefit_period ON public.tasks(benefit_period_id);")


def downgrade() -> None:
    # Repair migrations should not drop critical tables automatically.
    pass