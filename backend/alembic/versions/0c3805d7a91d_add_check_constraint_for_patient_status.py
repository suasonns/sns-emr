"""add check constraint for patient status

Revision ID: 0c3805d7a91d
Revises: aaf5da97782a
Create Date: 2026-05-26 16:20:52.833102

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0c3805d7a91d'
down_revision: Union[str, Sequence[str], None] = 'aaf5da97782a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Enforce allowed patient lifecycle states
    op.execute(
        """
        ALTER TABLE patients
        ADD CONSTRAINT patients_status_check
        CHECK (status IN ('ACTIVE', 'DISCHARGED', 'DECEASED'));
        """
    )


def downgrade():
    op.execute(
        """
        ALTER TABLE patients
        DROP CONSTRAINT IF EXISTS patients_status_check;
        """
    )
