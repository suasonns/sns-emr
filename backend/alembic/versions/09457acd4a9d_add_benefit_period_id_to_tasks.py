"""add benefit_period_id to tasks

Revision ID: 09457acd4a9d
Revises: eb76b663ad19
Create Date: 2026-05-29 19:06:44.495799
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "09457acd4a9d"
down_revision: Union[str, Sequence[str], None] = "eb76b663ad19"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(bind, table: str, column: str) -> bool:
    return bool(
        bind.execute(
            sa.text(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema='public'
                  AND table_name=:table
                  AND column_name=:column
                """
            ),
            {"table": table, "column": column},
        ).scalar()
    )


def _index_exists(bind, index_name: str) -> bool:
    return bool(
        bind.execute(
            sa.text(
                """
                SELECT 1
                FROM pg_indexes
                WHERE schemaname='public'
                  AND indexname=:idx
                """
            ),
            {"idx": index_name},
        ).scalar()
    )


def _fk_exists(bind, fk_name: str) -> bool:
    return bool(
        bind.execute(
            sa.text(
                """
                SELECT 1
                FROM information_schema.table_constraints
                WHERE table_schema='public'
                  AND table_name='tasks'
                  AND constraint_type='FOREIGN KEY'
                  AND constraint_name=:fk
                """
            ),
            {"fk": fk_name},
        ).scalar()
    )


def upgrade() -> None:
    bind = op.get_bind()

    # 1) Add nullable column only if missing
    if not _column_exists(bind, "tasks", "benefit_period_id"):
        op.add_column(
            "tasks",
            sa.Column("benefit_period_id", postgresql.UUID(as_uuid=True), nullable=True),
        )

    # 2) Add index only if missing
    if not _index_exists(bind, "ix_tasks_benefit_period_id"):
        op.create_index(
            "ix_tasks_benefit_period_id",
            "tasks",
            ["benefit_period_id"],
        )

    # 3) Conditionally add FK ONLY if benefit_periods.id is UUID and FK not already present
    id_type = bind.execute(
        sa.text(
            """
            SELECT data_type
            FROM information_schema.columns
            WHERE table_schema='public'
              AND table_name='benefit_periods'
              AND column_name='id'
            """
        )
    ).scalar()

    if id_type == "uuid" and not _fk_exists(bind, "fk_tasks_benefit_period_id"):
        op.create_foreign_key(
            "fk_tasks_benefit_period_id",
            "tasks",
            "benefit_periods",
            ["benefit_period_id"],
            ["id"],
        )


def downgrade() -> None:
    bind = op.get_bind()

    if _fk_exists(bind, "fk_tasks_benefit_period_id"):
        op.drop_constraint("fk_tasks_benefit_period_id", "tasks", type_="foreignkey")

    if _index_exists(bind, "ix_tasks_benefit_period_id"):
        op.drop_index("ix_tasks_benefit_period_id", table_name="tasks")

    if _column_exists(bind, "tasks", "benefit_period_id"):
        op.drop_column("tasks", "benefit_period_id")