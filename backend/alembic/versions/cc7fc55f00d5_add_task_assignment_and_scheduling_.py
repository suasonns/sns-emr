"""add task assignment and scheduling fields (rebuild-safe)

Revision ID: cc7fc55f00d5
Revises: 3b236f1a012b
Create Date: 2026-xx-xx xx:xx:xx.xxxxxx
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "cc7fc55f00d5"
down_revision: Union[str, Sequence[str], None] = "3b236f1a012b"
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


def _add_column_if_missing(table: str, column_sql: str, column_name: str) -> None:
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF to_regclass('public.' || :t) IS NOT NULL THEN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_schema='public'
                          AND table_name=:t
                          AND column_name=:c
                    ) THEN
                        EXECUTE format('ALTER TABLE public.%I ADD COLUMN %s', :t, :sql);
                    END IF;
                END IF;
            END $$;
            """
        ).bindparams(t=table, c=column_name, sql=column_sql)
    )


def upgrade() -> None:
    # If tasks table doesn't exist (should), do nothing
    if not _table_exists("tasks"):
        return

    # Add columns only if missing (idempotent)
    _add_column_if_missing("tasks", "assigned_user_id UUID NULL", "assigned_user_id")
    _add_column_if_missing("tasks", "scheduled_start_at TIMESTAMPTZ NULL", "scheduled_start_at")
    _add_column_if_missing("tasks", "schedule_status VARCHAR(32) NULL", "schedule_status")

    # Optional: indexes (safe)
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_tasks_assigned_user_id ON public.tasks(assigned_user_id)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_tasks_scheduled_start_at ON public.tasks(scheduled_start_at)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_tasks_schedule_status ON public.tasks(schedule_status)"))


def downgrade() -> None:
    # Forward-only / dev-safe no-op
    pass
