"""add_document_idg_resolution

Revision ID: 4aae5d46c5c4
Revises: b9b98b7f5f94
Create Date: 2026-05-21 09:30:43.359311

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '4aae5d46c5c4'
down_revision: Union[str, Sequence[str], None] = 'b9b98b7f5f94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "document_idg_resolution",
        sa.Column("document_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resolution_status", sa.String(length=32), nullable=False),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["public.document_records.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resolved_by"], ["public.users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["public.tenants.id"], ondelete="CASCADE"),
        schema="public",
    )

    op.create_index(
        "ix_document_idg_resolution_tenant_id",
        "document_idg_resolution",
        ["tenant_id"],
        unique=False,
        schema="public",
    )


def downgrade() -> None:
    op.drop_index("ix_document_idg_resolution_tenant_id", table_name="document_idg_resolution", schema="public")
    op.drop_table("document_idg_resolution", schema="public")