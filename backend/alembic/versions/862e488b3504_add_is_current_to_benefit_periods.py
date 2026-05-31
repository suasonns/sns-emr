"""add_is_current_to_benefit_periods

Revision ID: 862e488b3504
Revises: 797ff8cc7e5e
Create Date: 2026-05-30 09:33:52.341012

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '862e488b3504'
down_revision: Union[str, Sequence[str], None] = '797ff8cc7e5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    conn = op.get_bind()

    # ---------------------------------------------------------
    # Check if column already exists
    # ---------------------------------------------------------
    result = conn.execute(sa.text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'benefit_periods'
        AND column_name = 'is_current';
    """))

    column_exists = result.fetchone()

    # ---------------------------------------------------------
    # Add column ONLY if missing
    # ---------------------------------------------------------
    if not column_exists:
        op.add_column(
            "benefit_periods",
            sa.Column(
                "is_current",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
        )

    # ---------------------------------------------------------
    # Create partial unique index (ONLY if missing)
    # ---------------------------------------------------------
    result = conn.execute(sa.text("""
        SELECT indexname
        FROM pg_indexes
        WHERE tablename = 'benefit_periods'
        AND indexname = 'uq_one_current_bp_per_patient';
    """))

    index_exists = result.fetchone()

    if not index_exists:
        op.execute("""
            CREATE UNIQUE INDEX uq_one_current_bp_per_patient
            ON benefit_periods (patient_id)
            WHERE is_current = true;
        """)

def downgrade():
    op.execute("""
        DROP INDEX IF EXISTS uq_one_current_bp_per_patient;
    """)

    op.drop_column("benefit_periods", "is_current")