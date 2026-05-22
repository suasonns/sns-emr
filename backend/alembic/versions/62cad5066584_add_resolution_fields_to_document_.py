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

def upgrade():
    op.add_column(
        "document_notifications",
        sa.Column("resolution_status", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "document_notifications",
        sa.Column("resolution_note", sa.Text(), nullable=True),
    )
    op.add_column(
        "document_notifications",
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "document_notifications",
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Enforce allowed values at DB level (survey-defensible)
    op.create_check_constraint(
        "ck_document_notifications_resolution_status",
        "document_notifications",
        f"resolution_status IS NULL OR resolution_status IN {ALLOWED}",
    )

    # Helpful indexes for dashboards and survey exports
    op.create_index(
        "ix_document_notifications_document_id",
        "document_notifications",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        "ix_document_notifications_resolved_at",
        "document_notifications",
        ["resolved_at"],
        unique=False,
    )

def downgrade():
    op.drop_index("ix_document_notifications_resolved_at", table_name="document_notifications")
    op.drop_index("ix_document_notifications_document_id", table_name="document_notifications")
    op.drop_constraint("ck_document_notifications_resolution_status", "document_notifications", type_="check")

    op.drop_column("document_notifications", "resolved_by")
    op.drop_column("document_notifications", "resolved_at")
    op.drop_column("document_notifications", "resolution_note")
    op.drop_column("document_notifications", "resolution_status")