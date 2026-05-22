"""add_last_reminder_at_to_document_notifications

Revision ID: b9b98b7f5f94
Revises: 5bfed814030d
Create Date: 2026-05-21 08:20:25.420612

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b9b98b7f5f94'
down_revision: Union[str, Sequence[str], None] = '5bfed814030d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "document_notifications",
        sa.Column("last_reminder_at", sa.DateTime(timezone=True), nullable=True),
        schema="public",
    )


def downgrade() -> None:
    op.drop_column(
        "document_notifications",
        "last_reminder_at",
        schema="public",
    )