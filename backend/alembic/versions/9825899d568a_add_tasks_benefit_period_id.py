"""add tasks benefit_period_id (rebuild-safe)

Revision ID: 9825899d568a
Revises: cc7fc55f00d5
Create Date: 2026-xx-xx xx:xx:xx.xxxxxx
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "9825899d568a"
down_revision: Union[str, Sequence[str], None] = "cc7fc55f00d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table: str) -> bool:
    conn = op.get_bind()
    return bool(
        conn.execute(
            sa.text("SELECT to_regclass(:tbl) IS NOT NULL"),
            {"tbl": f"public.{table}"},
        ).scalar()
    )


def _has_column(table: str, column: str) -> bool:
    if not _table_exists(table):
        return False
    conn = op.get_bind()
    return bool(
        conn.execute(
            sa.text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema='public'
                      AND table_name=:t
                      AND column_name=:c
                )
                """
            ),
            {"t": table, "c": column},
        ).scalar()
    )


def upgrade() -> None:
    # If tasks doesn't exist (should), do nothing
    if not _table_exists("tasks"):
        return

    # Add benefit_period_id only if missing
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema='public'
                      AND table_name='tasks'
                      AND column_name='benefit_period_id'
                ) THEN
                    ALTER TABLE public.tasks
                      ADD COLUMN benefit_period_id UUID;
                END IF;
            END $$;
            """
        )
    )

    # Optional: add index if missing (safe)
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_tasks_benefit_period ON public.tasks(benefit_period_id);"
        )
    )

    # Optional: add FK only if both tables exist and constraint missing (safe)
    if _table_exists("benefit_periods"):
        op.execute(
            sa.text(
                """
                DO $$
                BEGIN
                  IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'fk_tasks_benefit_period_id'
                  ) THEN
                    ALTER TABLE public.tasks
                      ADD CONSTRAINT fk_tasks_benefit_period_id
                      FOREIGN KEY (benefit_period_id)
                      REFERENCES public.benefit_periods(id)
                      ON DELETE SET NULL;
                  END IF;
                END $$;
                """
            )
        )


def downgrade() -> None:
    # Forward-only / dev-safe no-op
    pass
