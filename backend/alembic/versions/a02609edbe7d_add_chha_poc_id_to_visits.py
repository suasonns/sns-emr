"""add chha_poc_id to visits

Revision ID: a02609edbe7d
Revises: 282649a795c2
Create Date: 2026-05-02 08:58:56.219830

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'a02609edbe7d'
down_revision: Union[str, Sequence[str], None] = '29a8d7b55bf5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "visits",
        sa.Column(
            "chha_poc_id",
            UUID(as_uuid=True),
            sa.ForeignKey("chha_pocs.id"),
            nullable=True,
        ),
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_visits_chha_poc_id ON visits(chha_poc_id);"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_visits_chha_poc_id;")
    op.drop_column("visits", "chha_poc_id")