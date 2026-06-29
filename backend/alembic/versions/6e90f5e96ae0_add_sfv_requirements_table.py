"""add_sfv_requirements_table

Revision ID: 6e90f5e96ae0
Revises: 76dca1229fdf
Create Date: 2026-06-24 00:40:47.423748

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6e90f5e96ae0'
down_revision: Union[str, Sequence[str], None] = '76dca1229fdf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'sfv_requirements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('triggering_visit_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        sa.Column('trigger_source', sa.String(), nullable=False),  # ICA, HUV1, HUV2
        
        sa.Column('symptom_type', sa.String(), nullable=True),  # pain, sob, etc
        sa.Column('symptom_severity', sa.String(), nullable=False),  # MODERATE/SEVERE
        
        sa.Column('trigger_date', sa.DateTime(), nullable=False),
        sa.Column('due_date', sa.DateTime(), nullable=False),
        
        sa.Column('status', sa.String(), nullable=False),  # PENDING, COMPLETED, MISSED
        sa.Column('completed_visit_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table('sfv_requirements')
