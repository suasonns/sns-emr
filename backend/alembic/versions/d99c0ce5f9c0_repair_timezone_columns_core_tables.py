"""repair: timezone columns core tables

Revision ID: d99c0ce5f9c0
Revises: c467b78906f9
Create Date: 2026-05-27 09:48:04.825695

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd99c0ce5f9c0'
down_revision: Union[str, Sequence[str], None] = 'c467b78906f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Patients
    op.alter_column(
        "patients",
        "created_at",
        type_=sa.DateTime(timezone=True),
        postgresql_using="created_at AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "patients",
        "updated_at",
        type_=sa.DateTime(timezone=True),
        postgresql_using="updated_at AT TIME ZONE 'UTC'",
    )

    # Visits
    op.alter_column(
        "visits",
        "visit_datetime",
        type_=sa.DateTime(timezone=True),
        postgresql_using="visit_datetime AT TIME ZONE 'UTC'",
    )


def downgrade():
    # Optional; often omitted in compliance-forward systems
    pass