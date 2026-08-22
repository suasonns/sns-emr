"""add missing facesheet payer type columns

Revision ID: b35658e9dca5
Revises: e2f558bae7ea
Create Date: 2026-08-22 03:53:57.122230

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b35658e9dca5'
down_revision: Union[str, Sequence[str], None] = 'e2f558bae7ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "patient_facesheet",
        sa.Column("primary_payer_type", sa.String(), nullable=True),
    )

    op.add_column(
        "patient_facesheet",
        sa.Column("secondary_payer_type", sa.String(), nullable=True),
    )


def downgrade():
    op.drop_column("patient_facesheet", "secondary_payer_type")
    op.drop_column("patient_facesheet", "primary_payer_type")