"""add physician directory and pecos cache

Revision ID: 9b7f6c4a1d2e
Revises: f2a4c0d9e1b7
Create Date: 2026-08-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "9b7f6c4a1d2e"
down_revision: Union[str, Sequence[str], None] = "f2a4c0d9e1b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "physicians",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("npi", sa.String(length=32), nullable=True),
        sa.Column("first_name", sa.String(length=120), nullable=True),
        sa.Column("last_name", sa.String(length=120), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=32), nullable=True),
        sa.Column("specialty_type", sa.String(length=255), nullable=True),
        sa.Column("license_number", sa.String(length=128), nullable=True),
        sa.Column("taxonomy_code", sa.String(length=64), nullable=True),
        sa.Column("address_street", sa.String(length=255), nullable=True),
        sa.Column("address_suite", sa.String(length=128), nullable=True),
        sa.Column("address_city", sa.String(length=120), nullable=True),
        sa.Column("address_state", sa.String(length=32), nullable=True),
        sa.Column("address_zip", sa.String(length=32), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("fax", sa.String(length=64), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("contact_name", sa.String(length=255), nullable=True),
        sa.Column("protocol_notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'active'")),
        sa.Column("register_for_eprescription", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("pecos_status", sa.String(length=32), nullable=True),
        sa.Column("pecos_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_physicians_tenant_id", "physicians", ["tenant_id"], unique=False)
    op.create_index("ix_physicians_npi", "physicians", ["npi"], unique=False)
    op.create_index("ix_physicians_display_name", "physicians", ["display_name"], unique=False)
    op.create_index("ix_physicians_status", "physicians", ["status"], unique=False)
    op.create_index("ix_physicians_tenant_status", "physicians", ["tenant_id", "status"], unique=False)
    op.create_index("ix_physicians_tenant_display_name", "physicians", ["tenant_id", "display_name"], unique=False)
    op.create_index("ix_physicians_tenant_npi", "physicians", ["tenant_id", "npi"], unique=False)

    op.create_table(
        "physician_pecos_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("npi", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=128), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refreshed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("npi"),
    )
    op.create_index("ix_physician_pecos_cache_npi", "physician_pecos_cache", ["npi"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_physician_pecos_cache_npi", table_name="physician_pecos_cache")
    op.drop_table("physician_pecos_cache")
    op.drop_index("ix_physicians_tenant_npi", table_name="physicians")
    op.drop_index("ix_physicians_tenant_display_name", table_name="physicians")
    op.drop_index("ix_physicians_tenant_status", table_name="physicians")
    op.drop_index("ix_physicians_status", table_name="physicians")
    op.drop_index("ix_physicians_display_name", table_name="physicians")
    op.drop_index("ix_physicians_npi", table_name="physicians")
    op.drop_index("ix_physicians_tenant_id", table_name="physicians")
    op.drop_table("physicians")
