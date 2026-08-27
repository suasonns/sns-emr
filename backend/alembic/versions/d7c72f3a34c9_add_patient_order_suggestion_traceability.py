"""add patient order suggestion traceability

Revision ID: d7c72f3a34c9
Revises: ec6af346493d
Create Date: 2026-08-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd7c72f3a34c9'
down_revision: Union[str, Sequence[str], None] = 'ec6af346493d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'patient_orders',
        sa.Column('source_kind', sa.String(length=32), nullable=False, server_default='MANUAL'),
    )
    op.add_column(
        'patient_orders',
        sa.Column('source_rnica_assessment_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        'ix_patient_orders_source_rnica_assessment_id',
        'patient_orders',
        ['source_rnica_assessment_id'],
    )
    op.create_foreign_key(
        'fk_patient_orders_source_rnica_assessment_id',
        'patient_orders',
        'rnica_assessments',
        ['source_rnica_assessment_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_patient_orders_source_rnica_assessment_id', 'patient_orders', type_='foreignkey')
    op.drop_index('ix_patient_orders_source_rnica_assessment_id', table_name='patient_orders')
    op.drop_column('patient_orders', 'source_rnica_assessment_id')
    op.drop_column('patient_orders', 'source_kind')
