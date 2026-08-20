"""add medication discontinue audit fields

Revision ID: 3f8a1c92d4e6
Revises: 6e4e89b3ed4b
Create Date: 2026-08-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "3f8a1c92d4e6"
down_revision: Union[str, Sequence[str], None] = "6e4e89b3ed4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("medications", sa.Column("discontinued_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("medications", sa.Column("discontinue_reason", sa.Text(), nullable=True))
    op.create_foreign_key(
        "fk_medications_discontinued_by_users",
        "medications",
        "users",
        ["discontinued_by"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_medications_discontinued_by_users", "medications", type_="foreignkey")
    op.drop_column("medications", "discontinue_reason")
    op.drop_column("medications", "discontinued_by")
