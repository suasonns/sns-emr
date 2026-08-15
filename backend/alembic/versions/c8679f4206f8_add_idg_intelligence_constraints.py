"""add idg intelligence constraints

Revision ID: c8679f4206f8
Revises: d5e9b8a683d7
Create Date: 2026-07-31 14:50:19.719239

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8679f4206f8'
down_revision: Union[str, Sequence[str], None] = 'd5e9b8a683d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():

    op.create_check_constraint(
        "ck_idg_intelligence_impact_level",
        "idg_intelligence_items",
        """
        idg_impact_level IS NULL
        OR idg_impact_level IN (
            'ADMINISTRATIVE',
            'CLINICAL',
            'SIGNIFICANT',
            'IDG_REQUIRED'
        )
        """
    )

    op.create_check_constraint(
        "ck_idg_intelligence_activation_route",
        "idg_intelligence_items",
        """
        activation_route IS NULL
        OR activation_route IN (
            'ADMIN_ONLY',
            'CLINICIAN_REVIEW',
            'MSW_REVIEW',
            'IDG_REVIEW_ONLY',
            'CLINICIAN_MD_REPORT',
            'CLINICIAN_ADMIN_MD_REPORT',
            'CLINICIAN_MSW_SC_AS_NEEDED',
            'ADMIN_CLINICIAN_REPORT',
            'CLINICIAN_OR_MSW_REVIEW'
        )
        """
    )


def downgrade():

    op.drop_constraint(
        "ck_idg_intelligence_activation_route",
        "idg_intelligence_items",
        type_="check",
    )

    op.drop_constraint(
        "ck_idg_intelligence_impact_level",
        "idg_intelligence_items",
        type_="check",
    )