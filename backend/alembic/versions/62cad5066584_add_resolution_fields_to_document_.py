"""add_resolution_fields_to_document_notifications

Revision ID: 62cad5066584
Revises: 4aae5d46c5c4
Create Date: 2026-05-21 10:45:59.579110

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '62cad5066584'
down_revision: Union[str, Sequence[str], None] = '4aae5d46c5c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ALLOWED = ("ACCEPTED", "NO_CHANGE", "OVERRIDDEN")

def upgrade() -> None:
    # Rebuild-safe: only apply if document_notifications exists
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF to_regclass('public.document_notifications') IS NOT NULL THEN
                    EXECUTE 'ALTER TABLE public.document_notifications
                             ADD COLUMN IF NOT EXISTS resolution_status VARCHAR(32)';
                    EXECUTE 'ALTER TABLE public.document_notifications
                             ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMPTZ';
                    EXECUTE 'ALTER TABLE public.document_notifications
                             ADD COLUMN IF NOT EXISTS resolved_by UUID';
                END IF;
            END $$;
            """
        )
    )

def downgrade():
    op.drop_index("ix_document_notifications_resolved_at", table_name="document_notifications")
    op.drop_index("ix_document_notifications_document_id", table_name="document_notifications")
    op.drop_constraint("ck_document_notifications_resolution_status", "document_notifications", type_="check")

    op.drop_column("document_notifications", "resolved_by")
    op.drop_column("document_notifications", "resolved_at")
    op.drop_column("document_notifications", "resolution_note")
    op.drop_column("document_notifications", "resolution_status")