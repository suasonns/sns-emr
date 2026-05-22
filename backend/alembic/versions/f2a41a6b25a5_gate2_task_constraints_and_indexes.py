"""gate2_task_constraints_and_indexes

Revision ID: f2a41a6b25a5
Revises: f115ffe3c4f9
Create Date: 2026-05-21 15:40:36.183650
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f2a41a6b25a5"
down_revision: Union[str, Sequence[str], None] = "f115ffe3c4f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Gate 2 — Task & Obligation Engine hard constraints

    Enforces the compliance-critical rule:
    - Evidence fields may only be present when status = COMPLETED
    - Evidence fields must be present when status = COMPLETED
    (Per Gate 2 blueprint and DoD) [1](https://suasonns-my.sharepoint.com/personal/romel_suason_suasonns_org/Documents/Microsoft%20Copilot%20Chat%20Files/SNS_EMR_Gate2_Task_Engine_Mini_Blueprint.md)[2](https://suasonns-my.sharepoint.com/personal/romel_suason_suasonns_org/Documents/Microsoft%20Copilot%20Chat%20Files/SNS_EMR_Definition_of_Done_By_Gate%20%281%29.md)
    """

    # ---------------------------------------------------------
    # 1) Evidence enforcement (CRITICAL)
    #
    # Rule:
    # - If status = COMPLETED:
    #     completed_at IS NOT NULL
    #     completion_reference_type IS NOT NULL
    #     completion_reference_id IS NOT NULL
    # - If status != COMPLETED:
    #     ALL of the above MUST be NULL
    #
    # NOTE: status is an ENUM in your DB, so we only reference the valid label 'COMPLETED'.
    # ---------------------------------------------------------
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'ck_tasks_completed_requires_evidence'
        ) THEN
            ALTER TABLE public.tasks
            ADD CONSTRAINT ck_tasks_completed_requires_evidence
            CHECK (
                (
                    status = 'COMPLETED'
                    AND completed_at IS NOT NULL
                    AND completion_reference_type IS NOT NULL
                    AND completion_reference_id IS NOT NULL
                )
                OR
                (
                    status <> 'COMPLETED'
                    AND completed_at IS NULL
                    AND completion_reference_type IS NULL
                    AND completion_reference_id IS NULL
                )
            );
        END IF;
    END $$;
    """)

    # ---------------------------------------------------------
    # 2) Performance indexes (tenant dashboards / overdue scans)
    # ---------------------------------------------------------
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_tasks_tenant_status_due
        ON public.tasks (tenant_id, status, due_date);
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_tasks_tenant_patient
        ON public.tasks (tenant_id, patient_id);
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_tasks_completion_reference
        ON public.tasks (completion_reference_id);
    """)


def downgrade() -> None:
    """
    Compliance-first: do not remove constraints/indexes in downgrade.
    """
    pass