"""prevent duplicate active POC_UPDATE per benefit period

Revision ID: 42261e766b25
Revises: e8b243e6832b
Create Date: 2026-05-09 10:58:04.314117

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '42261e766b25'
down_revision: Union[str, Sequence[str], None] = 'e8b243e6832b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    index_name = "uq_tasks_active_poc_update_per_bp"

    index_exists = bind.execute(
        text("""
            SELECT EXISTS (
              SELECT 1
              FROM pg_indexes
              WHERE schemaname='public'
                AND indexname=:idx
            );
        """),
        {"idx": index_name},
    ).scalar()

    if not index_exists:
        op.create_index(
            index_name,
            "tasks",
            ["tenant_id", "patient_id", "benefit_period_id"],
            unique=True,
            postgresql_where=sa.text(
                "task_type = 'POC_UPDATE' "
                "AND benefit_period_id IS NOT NULL "
                "AND status IN ('PENDING', 'OVERDUE', 'ESCALATED')"
            ),
        )


def downgrade() -> None:
    # Conservative downgrade
    pass