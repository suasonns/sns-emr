"""add benefit_period_id to tasks (repair-safe)

Revision ID: 25aebf89a1ae
Revises: 2d942d7ead24
Create Date: 2026-05-09 10:09:44.574017
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

revision: str = "25aebf89a1ae"
down_revision: Union[str, Sequence[str], None] = "2d942d7ead24"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # 1) Column exists?
    column_exists = bind.execute(
        text("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema='public'
                  AND table_name='tasks'
                  AND column_name='benefit_period_id'
            );
        """)
    ).scalar()

    if not column_exists:
        op.add_column(
            "tasks",
            sa.Column("benefit_period_id", postgresql.UUID(as_uuid=True), nullable=True),
        )

    # 2) Index exists?
    index_exists = bind.execute(
        text("""
            SELECT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname='public'
                  AND tablename='tasks'
                  AND indexname='ix_tasks_benefit_period_id'
            );
        """)
    ).scalar()

    if not index_exists:
        op.create_index(
            "ix_tasks_benefit_period_id",
            "tasks",
            ["benefit_period_id"],
        )

    # 3) FK exists?
    fk_exists = bind.execute(
        text("""
            SELECT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname='fk_tasks_benefit_period_id'
            );
        """)
    ).scalar()

    if not fk_exists:
        op.create_foreign_key(
            "fk_tasks_benefit_period_id",
            source_table="tasks",
            referent_table="benefit_periods",
            local_cols=["benefit_period_id"],
            remote_cols=["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    # Conservative downgrade for EMR safety
    pass