"""add tasks benefit_period_id

Revision ID: 9825899d568a
Revises: cc7fc55f00d5
Create Date: 2026-05-26 19:31:25.874717

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9825899d568a'
down_revision: Union[str, Sequence[str], None] = 'cc7fc55f00d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "tasks",
        sa.Column("benefit_period_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    op.create_index(
        "ix_tasks_benefit_period_id",
        "tasks",
        ["benefit_period_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_tasks_benefit_period_id_benefit_periods",
        "tasks",
        "benefit_periods",
        ["benefit_period_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint(
        "fk_tasks_benefit_period_id_benefit_periods",
        "tasks",
        type_="foreignkey",
    )

    op.drop_index("ix_tasks_benefit_period_id", table_name="tasks")
    op.drop_column("tasks", "benefit_period_id")
