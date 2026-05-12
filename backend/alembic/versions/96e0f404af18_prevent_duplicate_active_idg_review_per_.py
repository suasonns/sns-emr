"""prevent duplicate active IDG_REVIEW per benefit period

Revision ID: 96e0f404af18
Revises: 42261e766b25
Create Date: 2026-05-09 11:07:53.853007

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '96e0f404af18'
down_revision: Union[str, Sequence[str], None] = '42261e766b25'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    index_name = "uq_tasks_active_idg_review_per_bp"

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
                "task_type = 'IDG_REVIEW' "
                "AND benefit_period_id IS NOT NULL "
                "AND status IN ('PENDING', 'OVERDUE', 'ESCALATED')"
            ),
        )


def downgrade() -> None:
    # Conservative downgrade
    pass