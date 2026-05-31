"""add_idg_review_to_tasks_regulatory_basis_enum

Revision ID: 52b9a117e2bb
Revises: 3b66961d337c
Create Date: 2026-05-29 18:12:39.411445

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '52b9a117e2bb'
down_revision: Union[str, Sequence[str], None] = '3b66961d337c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    op.execute("ALTER TYPE tasks_regulatory_basis_enum ADD VALUE IF NOT EXISTS 'IDG_REVIEW';")


def downgrade() -> None:
    # Postgres enums cannot safely remove values.
    pass
