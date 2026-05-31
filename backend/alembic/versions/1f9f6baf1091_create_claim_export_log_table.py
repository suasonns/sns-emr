"""create claim_export_log table

Revision ID: 1f9f6baf1091
Revises: 4f7d7c237580
Create Date: 2026-05-30 20:00:17.155370
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = '1f9f6baf1091'
down_revision: Union[str, Sequence[str], None] = '4f7d7c237580'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'claim_export_log',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('patient_id', sa.String(), nullable=False),
        sa.Column('billing_cycle_id', sa.String(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),

        sa.Column('override_used', sa.Boolean(), nullable=True),
        sa.Column('override_reason', sa.String(), nullable=True),

        sa.Column('created_at', sa.DateTime(), nullable=False)
    )


def downgrade():
    op.drop_table('claim_export_log')