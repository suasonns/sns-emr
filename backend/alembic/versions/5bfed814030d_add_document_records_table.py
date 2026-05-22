"""add_document_records_table

Revision ID: 5bfed814030d
Revises: 20c4ae0e84b3
Create Date: 2026-05-20 20:29:22.552689

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '5bfed814030d'
down_revision: Union[str, Sequence[str], None] = '20c4ae0e84b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)

    # ✅ Idempotent: if table already exists, do nothing
    if insp.has_table("document_records"):
        return

    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    op.create_table(
        "document_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_type", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="EXTERNAL"),
        sa.Column("file_name", sa.String(length=255), nullable=True),
        sa.Column("file_path", sa.String(length=512), nullable=True),
        sa.Column("extracted_values", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("document_text", sa.Text(), nullable=True),
        sa.Column("is_flagged", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("flag_tier", sa.String(length=16), nullable=True),
        sa.Column("matched_rule_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="SET NULL"),
    )

    op.create_index("ix_document_records_tenant_id", "document_records", ["tenant_id"])
    op.create_index("ix_document_records_patient_id", "document_records", ["patient_id"])
    op.create_index("ix_document_records_document_type", "document_records", ["document_type"])
    op.create_index("ix_document_records_is_flagged", "document_records", ["is_flagged"])

def downgrade() -> None:
    op.drop_index("ix_document_records_is_flagged", table_name="document_records")
    op.drop_index("ix_document_records_document_type", table_name="document_records")
    op.drop_index("ix_document_records_patient_id", table_name="document_records")
    op.drop_index("ix_document_records_tenant_id", table_name="document_records")
    op.drop_table("document_records")