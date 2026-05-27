"""repair tasks add discipline, regulatory_basis, alert_reason, created_by (rebuild-safe)

Revision ID: a0bb66070697
Revises: 9825899d568a
Create Date: 2026-05-26 19:35:41.868065
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a0bb66070697"
down_revision: Union[str, Sequence[str], None] = "9825899d568a"
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


def _add_column_if_missing(table: str, column_name: str, column_sql: str) -> None:
    """
    Enterprise‑grade, rebuild‑safe ADD COLUMN.
    - Table must exist
    - Column must be missing
    """
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF to_regclass('public.' || :t) IS NOT NULL THEN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND table_name   = :t
                          AND column_name  = :c
                    ) THEN
                        EXECUTE format(
                            'ALTER TABLE public.%I ADD COLUMN %s',
                            :t,
                            :sql
                        );
                    END IF;
                END IF;
            END $$;
            """
        ).bindparams(t=table, c=column_name, sql=column_sql)
    )


def upgrade() -> None:
    # If tasks table does not exist in this rebuild path, skip safely
    if not _table_exists("tasks"):
        return

    # Add columns idempotently
    _add_column_if_missing("tasks", "discipline", "discipline VARCHAR(16)")
    _add_column_if_missing("tasks", "regulatory_basis", "regulatory_basis VARCHAR(64)")
    _add_column_if_missing("tasks", "alert_reason", "alert_reason VARCHAR(255)")
    _add_column_if_missing("tasks", "created_by", "created_by UUID")

    # Indexes (safe / idempotent)
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_tasks_discipline "
            "ON public.tasks(discipline)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_tasks_regulatory_basis "
            "ON public.tasks(regulatory_basis)"
        )
    )


def downgrade() -> None:
    # Forward‑only / dev‑safe no‑op
    pass