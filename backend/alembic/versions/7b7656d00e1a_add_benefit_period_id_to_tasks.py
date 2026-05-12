"""add benefit_period_id to tasks

Revision ID: 7b7656d00e1a
Revises: 3c67f6f12c0d
Create Date: 2026-05-05 12:54:38.159411

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b7656d00e1a'
down_revision: Union[str, Sequence[str], None] = '3c67f6f12c0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add benefit_period_id only if missing (idempotent)
    op.execute("""
    ALTER TABLE public.tasks
      ADD COLUMN IF NOT EXISTS benefit_period_id UUID;
    """)

    # Add FK only if benefit_periods exists and constraint is missing
    op.execute("""
    DO $$
    BEGIN
      IF to_regclass('public.benefit_periods') IS NOT NULL THEN
        IF NOT EXISTS (
          SELECT 1 FROM pg_constraint
          WHERE conname = 'tasks_benefit_period_id_fkey'
        ) THEN
          ALTER TABLE public.tasks
            ADD CONSTRAINT tasks_benefit_period_id_fkey
            FOREIGN KEY (benefit_period_id)
            REFERENCES public.benefit_periods(id);
        END IF;
      END IF;
    END $$;
    """)

def downgrade():
    op.drop_index("ix_tasks_benefit_period", table_name="tasks")
    op.drop_constraint("fk_tasks_benefit_period", "tasks", type_="foreignkey")
    op.drop_column("tasks", "benefit_period_id")