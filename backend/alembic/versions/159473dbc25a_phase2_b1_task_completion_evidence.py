"""phase2_b1_task_completion_evidence

Enforces compliance rule:
A task marked COMPLETED must have completion evidence.

Required when status = 'COMPLETED':
- completed_at
- completion_reference_type
- completion_reference_id

This is CMS / ACHC / CHAP survey-defensible enforcement.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "159473dbc25a"
down_revision: Union[str, Sequence[str], None] = "2611c820fc34"
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


# -------------------------------------------------------------------
# Helpers (PostgreSQL-safe, idempotent, rebuild-safe)
# -------------------------------------------------------------------
def _add_column_if_missing(table_name: str, column_sql: str, column_name: str) -> None:
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
                          AND table_name = :t
                          AND column_name = :c
                    ) THEN
                        EXECUTE format(
                            'ALTER TABLE public.%I ADD COLUMN %s',
                            :t,
                            :sql
                        );
                    END IF;
                END IF;
            END
            $$;
            """
        ).bindparams(t=table_name, c=column_name, sql=column_sql)
    )


def _add_constraint_if_missing(table_name: str, constraint_name: str, constraint_sql: str) -> None:
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF to_regclass('public.' || :t) IS NOT NULL THEN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM pg_constraint
                        WHERE conname = :con
                    ) THEN
                        EXECUTE format(
                            'ALTER TABLE public.%I ADD CONSTRAINT %I %s',
                            :t,
                            :con,
                            :sql
                        );
                    END IF;
                END IF;
            END
            $$;
            """
        ).bindparams(t=table_name, con=constraint_name, sql=constraint_sql)
    )


def _create_index_if_missing(index_name: str, index_sql: str) -> None:
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                      AND indexname = :ix
                ) THEN
                    EXECUTE :sql;
                END IF;
            END
            $$;
            """
        ).bindparams(ix=index_name, sql=index_sql)
    )


# -------------------------------------------------------------------
# Upgrade
# -------------------------------------------------------------------
def upgrade() -> None:
    # If tasks does not exist (should not happen), skip safely
    if not _table_exists("tasks"):
        return

    # Add completion evidence columns (nullable; enforced by CHECK)
    _add_column_if_missing("tasks", "completed_at TIMESTAMPTZ NULL", "completed_at")
    _add_column_if_missing("tasks", "completion_reference_type VARCHAR(20) NULL", "completion_reference_type")
    _add_column_if_missing("tasks", "completion_reference_id UUID NULL", "completion_reference_id")

    # Enforce: COMPLETED requires evidence
    _add_constraint_if_missing(
        "tasks",
        "ck_tasks_completed_requires_evidence",
        (
            "CHECK ("
            "status <> 'COMPLETED' "
            "OR ("
            "completed_at IS NOT NULL "
            "AND completion_reference_type IS NOT NULL "
            "AND completion_reference_id IS NOT NULL"
            ")"
            ")"
        ),
    )

    # Enforce allowed evidence types (ENUM-SAFE):
    # Cast to text so Postgres does not treat literals as enum values (avoids UnsafeNewEnumValueUsage).
    _add_constraint_if_missing(
        "tasks",
        "ck_tasks_completion_reference_type_allowed",
        (
            "CHECK ("
            "completion_reference_type IS NULL "
            "OR completion_reference_type::text IN ('VISIT', 'NOTE', 'DOCUMENT')"
            ")"
        ),
    )

    # Helpful indexes for audit + reporting
    _create_index_if_missing(
        "idx_tasks_completed_at",
        "CREATE INDEX IF NOT EXISTS idx_tasks_completed_at ON public.tasks (completed_at)",
    )
    _create_index_if_missing(
        "idx_tasks_completion_reference",
        (
            "CREATE INDEX IF NOT EXISTS idx_tasks_completion_reference "
            "ON public.tasks (completion_reference_type, completion_reference_id)"
        ),
    )


# -------------------------------------------------------------------
# Downgrade
# -------------------------------------------------------------------
def downgrade() -> None:
    # Forward-only by design.
    pass