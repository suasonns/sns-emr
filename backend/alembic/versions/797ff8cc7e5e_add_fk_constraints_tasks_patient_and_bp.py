"""add_fk_constraints_tasks_patient_and_bp

Revision ID: 797ff8cc7e5e
Revises: 09457acd4a9d
Create Date: 2026-05-30 08:55:12.744456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '797ff8cc7e5e'
down_revision: Union[str, Sequence[str], None] = '09457acd4a9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    conn = op.get_bind()

    # ---------------------------------------------
    # FK: tasks.patient_id → patients.id
    # ---------------------------------------------
    result = conn.execute(sa.text("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'tasks'
          AND constraint_type = 'FOREIGN KEY'
          AND constraint_name = 'fk_tasks_patient_id';
    """))

    if not result.fetchone():
        op.create_foreign_key(
            "fk_tasks_patient_id",
            "tasks",
            "patients",
            ["patient_id"],
            ["id"],
            ondelete="RESTRICT"
        )

    # ---------------------------------------------
    # FK: tasks.benefit_period_id → benefit_periods.id
    # ---------------------------------------------
    result = conn.execute(sa.text("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'tasks'
          AND constraint_type = 'FOREIGN KEY'
          AND constraint_name = 'fk_tasks_benefit_period_id';
    """))

    if not result.fetchone():
        op.create_foreign_key(
            "fk_tasks_benefit_period_id",
            "tasks",
            "benefit_periods",
            ["benefit_period_id"],
            ["id"],
            ondelete="SET NULL"
        )

def downgrade():
    op.drop_constraint("fk_tasks_benefit_period_id", "tasks", type_="foreignkey")
    op.drop_constraint("fk_tasks_patient_id", "tasks", type_="foreignkey")