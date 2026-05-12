"""add_regulatory_basis_idg_15_day

Revision ID: 515c21f1f8de
Revises: 13d23132e68c
Create Date: 2026-05-07 16:37:38.424331

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '515c21f1f8de'
down_revision: Union[str, Sequence[str], None] = '13d23132e68c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    DO $$
    BEGIN
        ALTER TYPE tasks_regulatory_basis_enum ADD VALUE 'IDG_15_DAY';
    EXCEPTION
        WHEN duplicate_object THEN NULL;
    END$$;
    """)

def downgrade() -> None:
    # no-op: Postgres cannot safely remove enum values
    pass
