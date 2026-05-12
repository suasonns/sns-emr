"""add_unique_constraint_to_regulatory_report_metrics

Revision ID: ab9b61a7b73f
Revises: e83a93644f10
Create Date: 2026-05-05 19:31:22.158366

"""

from typing import Sequence, Union
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'ab9b61a7b73f'
down_revision: Union[str, Sequence[str], None] = 'e83a93644f10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade():
    op.create_unique_constraint(
        'uq_regulatory_report_metrics_report_section_key',
        'regulatory_report_metrics',
        ['report_id', 'section_id', 'metric_key']
    )


def downgrade():
    op.drop_constraint(
        'uq_regulatory_report_metrics_report_section_key',
        'regulatory_report_metrics',
        type_='unique'
    )
