"""repair: timezone users timestamps

Revision ID: c06467c1e1cb
Revises: b158ac923154
Create Date: 2026-05-27 09:58:14.812349

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c06467c1e1cb'
down_revision: Union[str, Sequence[str], None] = 'b158ac923154'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column(
        "users", "created_at",
        type_=sa.DateTime(timezone=True),
        postgresql_using="created_at AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "users", "updated_at",
        type_=sa.DateTime(timezone=True),
        postgresql_using="updated_at AT TIME ZONE 'UTC'",
    )

def downgrade():
    pass