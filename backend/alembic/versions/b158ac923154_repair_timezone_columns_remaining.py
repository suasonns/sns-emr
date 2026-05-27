"""repair: timezone columns remaining

Revision ID: b158ac923154
Revises: d99c0ce5f9c0
Create Date: 2026-05-27 09:53:26.138577

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b158ac923154'
down_revision: Union[str, Sequence[str], None] = 'd99c0ce5f9c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Benefit periods
    op.alter_column(
        "benefit_periods", "created_at",
        type_=sa.DateTime(timezone=True),
        postgresql_using="created_at AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "benefit_periods", "updated_at",
        type_=sa.DateTime(timezone=True),
        postgresql_using="updated_at AT TIME ZONE 'UTC'",
    )

    # Document records
    op.alter_column(
        "document_records", "created_at",
        type_=sa.DateTime(timezone=True),
        postgresql_using="created_at AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "document_records", "updated_at",
        type_=sa.DateTime(timezone=True),
        postgresql_using="updated_at AT TIME ZONE 'UTC'",
    )

    # Tasks
    op.alter_column(
        "tasks", "created_at",
        type_=sa.DateTime(timezone=True),
        postgresql_using="created_at AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "tasks", "updated_at",
        type_=sa.DateTime(timezone=True),
        postgresql_using="updated_at AT TIME ZONE 'UTC'",
    )

    # IDG reviews
    op.alter_column(
        "idg_reviews", "created_at",
        type_=sa.DateTime(timezone=True),
        postgresql_using="created_at AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "idg_reviews", "updated_at",
        type_=sa.DateTime(timezone=True),
        postgresql_using="updated_at AT TIME ZONE 'UTC'",
    )

    # Visits (remaining timestamp columns)
    op.alter_column(
        "visits", "finalized_at",
        type_=sa.DateTime(timezone=True),
        postgresql_using="finalized_at AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "visits", "created_at",
        type_=sa.DateTime(timezone=True),
        postgresql_using="created_at AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "visits", "updated_at",
        type_=sa.DateTime(timezone=True),
        postgresql_using="updated_at AT TIME ZONE 'UTC'",
    )

    # Survey access
    op.alter_column(
        "survey_access", "created_at",
        type_=sa.DateTime(timezone=True),
        postgresql_using="created_at AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "survey_access", "updated_at",
        type_=sa.DateTime(timezone=True),
        postgresql_using="updated_at AT TIME ZONE 'UTC'",
    )

    # Eligibility decisions
    op.alter_column(
        "eligibility_decisions", "decision_timestamp",
        type_=sa.DateTime(timezone=True),
        postgresql_using="decision_timestamp AT TIME ZONE 'UTC'",
    )

def downgrade():
    pass