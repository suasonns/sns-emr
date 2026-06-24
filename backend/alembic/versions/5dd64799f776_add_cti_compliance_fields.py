"""add CTI compliance fields

Revision ID: 5dd64799f776
Revises: 6c725d29cdaf
Create Date: 2026-06-22 14:02:22.488211

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5dd64799f776'
down_revision: Union[str, Sequence[str], None] = '6c725d29cdaf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('certifications', sa.Column('certification_type', sa.String(), nullable=True))
    op.add_column('certifications', sa.Column('effective_start_date', sa.Date(), nullable=True))
    op.add_column('certifications', sa.Column('effective_end_date', sa.Date(), nullable=True))
    op.add_column('certifications', sa.Column('primary_dx', sa.String(), nullable=True))
    op.add_column('certifications', sa.Column('narrative', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('certifications', 'narrative')
    op.drop_column('certifications', 'primary_dx')
    op.drop_column('certifications', 'effective_end_date')
    op.drop_column('certifications', 'effective_start_date')
    op.drop_column('certifications', 'certification_type')
