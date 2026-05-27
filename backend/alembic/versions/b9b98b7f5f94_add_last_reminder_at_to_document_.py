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
    # Rebuild-safe: only apply if the table exists in this branch/order
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF to_regclass('public.document_notifications') IS NOT NULL THEN
                    EXECUTE 'ALTER TABLE public.document_notifications
                             ADD COLUMN IF NOT EXISTS last_reminder_at TIMESTAMPTZ';
                END IF;
            END $$;
            """
        )
    )


def downgrade() -> None:
    op.drop_column(
        "document_notifications",
        "last_reminder_at",
        schema="public",
    )