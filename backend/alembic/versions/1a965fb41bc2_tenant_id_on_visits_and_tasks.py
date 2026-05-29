"""tenant_id_on_visits_and_tasks

Forward-only migration.
Adds tenant_id to visits and tasks, backfills from patients (or users via created_by),
and enforces NOT NULL to lock tenant isolation.

This migration is idempotent across environments via IF NOT EXISTS SQL.
"""

from __future__ import annotations

from alembic import op

revision = "1a965fb41bc2"
down_revision = "60a0912e0f06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -----------------------------------------
    # 1) Add tenant_id columns (idempotent)
    # -----------------------------------------
    op.execute("ALTER TABLE public.visits ADD COLUMN IF NOT EXISTS tenant_id uuid;")
    op.execute("ALTER TABLE public.tasks ADD COLUMN IF NOT EXISTS tenant_id uuid;")

    # -----------------------------------------
    # 2) Backfill visits.tenant_id from patients
    # -----------------------------------------
    op.execute(
        """
        UPDATE public.visits v
        SET tenant_id = p.tenant_id
        FROM public.patients p
        WHERE v.tenant_id IS NULL
          AND v.patient_id = p.id;
        """
    )

    # -----------------------------------------
    # 3) Backfill tasks.tenant_id
    # Priority:
    #   a) from patients if task.patient_id exists
    #   b) else from users via created_by (if present)
    # -----------------------------------------
    op.execute(
        """
        UPDATE public.tasks t
        SET tenant_id = p.tenant_id
        FROM public.patients p
        WHERE t.tenant_id IS NULL
          AND t.patient_id = p.id;
        """
    )

    op.execute(
        """
        UPDATE public.tasks t
        SET tenant_id = u.tenant_id
        FROM public.users u
        WHERE t.tenant_id IS NULL
          AND t.created_by = u.id;
        """
    )

    # -----------------------------------------
    # 4) Fail loudly if any rows are still NULL
    # (prevents "invisible data" later)
    # -----------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM public.visits WHERE tenant_id IS NULL) THEN
                RAISE EXCEPTION 'Tenant hardening failed: visits.tenant_id still NULL for some rows. Backfill required.';
            END IF;

            IF EXISTS (SELECT 1 FROM public.tasks WHERE tenant_id IS NULL) THEN
                RAISE EXCEPTION 'Tenant hardening failed: tasks.tenant_id still NULL for some rows. Backfill required.';
            END IF;
        END $$;
        """
    )

    # -----------------------------------------
    # 5) Enforce NOT NULL (locks isolation)
    # -----------------------------------------
    op.execute("ALTER TABLE public.visits ALTER COLUMN tenant_id SET NOT NULL;")
    op.execute("ALTER TABLE public.tasks ALTER COLUMN tenant_id SET NOT NULL;")

    # -----------------------------------------
    # 6) Indexes (idempotent)
    # -----------------------------------------
    op.execute("CREATE INDEX IF NOT EXISTS ix_visits_tenant_id ON public.visits (tenant_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tasks_tenant_id ON public.tasks (tenant_id);")

    # -----------------------------------------
    # 7) Foreign keys (idempotent via conditional DO blocks)
    # -----------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_visits_tenant_id'
            ) THEN
                ALTER TABLE public.visits
                ADD CONSTRAINT fk_visits_tenant_id
                FOREIGN KEY (tenant_id) REFERENCES public.tenants(id)
                ON DELETE RESTRICT;
            END IF;
        END $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_tasks_tenant_id'
            ) THEN
                ALTER TABLE public.tasks
                ADD CONSTRAINT fk_tasks_tenant_id
                FOREIGN KEY (tenant_id) REFERENCES public.tenants(id)
                ON DELETE RESTRICT;
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    # Forward-only migration
    pass