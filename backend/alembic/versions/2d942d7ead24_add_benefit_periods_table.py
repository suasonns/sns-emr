"""add benefit_periods table (repair-safe)

Revision ID: 2d942d7ead24
Revises: 807e79ef13b2
Create Date: 2026-05-09 10:02:22.060276
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "2d942d7ead24"
down_revision: Union[str, Sequence[str], None] = "807e79ef13b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # 1) Create table only if it does NOT exist
    table_exists = bind.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'benefit_periods'
            );
            """
        )
    ).scalar()

    if not table_exists:
        op.create_table(
            "benefit_periods",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("start_date", sa.Date, nullable=False),
            sa.Column("end_date", sa.Date, nullable=True),
            sa.Column("benefit_period_number", sa.Integer, nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        )

    # 2) Create index only if it does NOT exist
    index_exists = bind.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'public'
                  AND indexname = 'ix_benefit_periods_patient_id'
            );
            """
        )
    ).scalar()

    if not index_exists:
        op.create_index(
            "ix_benefit_periods_patient_id",
            "benefit_periods",
            ["patient_id"],
        )


def downgrade() -> None:
    # Conservative downgrade: do NOT drop clinical tables automatically.
    # If you truly need removal in a dev database, uncomment below.
    #
    # op.drop_index("ix_benefit_periods_patient_id", table_name="benefit_periods")
    # op.drop_table("benefit_periods")
    pass