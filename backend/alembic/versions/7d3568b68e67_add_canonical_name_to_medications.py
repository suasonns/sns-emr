"""add canonical_name to medications

Revision ID: 7d3568b68e67
Revises: bc7333a484b1
Create Date: 2026-05-03 12:52:38.246492

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d3568b68e67'
down_revision: Union[str, Sequence[str], None] = 'bc7333a484b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Column already exists in DB in this environment; make migration safe everywhere.
    op.execute(
        "ALTER TABLE medications "
        "ADD COLUMN IF NOT EXISTS canonical_name VARCHAR(255)"
    )

    # IMPORTANT: use the index name that already exists in your DB
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_medications_canonical_name "
        "ON medications (canonical_name)"
    )

def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_medications_canonical_name")
    op.execute("ALTER TABLE medications DROP COLUMN IF EXISTS canonical_name")