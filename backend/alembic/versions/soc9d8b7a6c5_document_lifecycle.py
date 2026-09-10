"""Document lifecycle -- soft delete / archive / restore for document_records.

Priority 1 of the documented Benefit Period / Document Harvest workflow
(see docs/workflows/BenefitPeriodWorkflow.md and companions). Documents are
never permanently deleted -- this migration adds the lifecycle_status state
machine plus the per-transition audit columns.

Purely additive: no existing column is dropped or altered, every new
column is nullable or has a safe server_default, so existing rows and
existing code paths are unaffected.

Revision ID: soc9d8b7a6c5
Revises: y2z3a4b5c6d7
Create Date: 2026-09-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "soc9d8b7a6c5"
down_revision: Union[str, Sequence[str], None] = "y2z3a4b5c6d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "document_records",
        sa.Column(
            "lifecycle_status",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'ACTIVE'"),
        ),
    )
    op.add_column(
        "document_records",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "document_records",
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "document_records",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "document_records",
        sa.Column("archived_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "document_records",
        sa.Column("restored_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "document_records",
        sa.Column("restored_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_document_records_lifecycle_status",
        "document_records",
        ["lifecycle_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_document_records_lifecycle_status", table_name="document_records")
    op.drop_column("document_records", "restored_by")
    op.drop_column("document_records", "restored_at")
    op.drop_column("document_records", "archived_by")
    op.drop_column("document_records", "archived_at")
    op.drop_column("document_records", "deleted_by")
    op.drop_column("document_records", "deleted_at")
    op.drop_column("document_records", "lifecycle_status")
