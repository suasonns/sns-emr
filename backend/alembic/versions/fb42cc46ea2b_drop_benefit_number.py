"""drop benefit_number

Revision ID: fb42cc46ea2b
Revises: 31d52818353a
Create Date: 2026-05-30 11:15:59.629426

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fb42cc46ea2b'
down_revision: Union[str, Sequence[str], None] = '31d52818353a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    conn = op.get_bind()

    # Safety check
    result = conn.execute(sa.text("""
        SELECT COUNT(*)
        FROM benefit_periods
        WHERE benefit_number IS DISTINCT FROM period_number
    """)).scalar()

    if result != 0:
        raise Exception("Mismatch between benefit_number and period_number")

    op.drop_column("benefit_periods", "benefit_number")


def downgrade():
    op.add_column(
        "benefit_periods",
        sa.Column("benefit_number", sa.Integer(), nullable=True),
    )

    op.execute("""
        UPDATE benefit_periods
        SET benefit_number = period_number
    """)

    op.alter_column(
        "benefit_periods",
        "benefit_number",
        nullable=False,
    )