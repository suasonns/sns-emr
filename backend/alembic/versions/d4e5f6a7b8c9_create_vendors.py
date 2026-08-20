"""create vendors table (Pharmacy/DME/Laboratory/AL/Contracted Staff directory)

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vendors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vendor_type", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("ncpdp_id", sa.String(length=32), nullable=True),
        sa.Column("address_street", sa.String(length=255), nullable=True),
        sa.Column("address_city", sa.String(length=120), nullable=True),
        sa.Column("address_state", sa.String(length=32), nullable=True),
        sa.Column("address_zip", sa.String(length=32), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("fax", sa.String(length=64), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("contact_person", sa.String(length=255), nullable=True),
        sa.Column("npi", sa.String(length=32), nullable=True),
        sa.Column("npi_exp_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rx_state_lic", sa.String(length=128), nullable=True),
        sa.Column("rx_state_lic_exp_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("bus_lic", sa.String(length=128), nullable=True),
        sa.Column("bus_lic_exp_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("insurance", sa.String(length=128), nullable=True),
        sa.Column("insurance_exp_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'active'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_vendors_tenant_id", "vendors", ["tenant_id"], unique=False)
    op.create_index("ix_vendors_tenant_status", "vendors", ["tenant_id", "status"], unique=False)
    op.create_index("ix_vendors_tenant_name", "vendors", ["tenant_id", "name"], unique=False)
    op.create_index("ix_vendors_tenant_type", "vendors", ["tenant_id", "vendor_type"], unique=False)
    op.create_index("ix_vendors_tenant_npi", "vendors", ["tenant_id", "npi"], unique=False)
    op.create_index("ix_vendors_name", "vendors", ["name"], unique=False)
    op.create_index("ix_vendors_vendor_type", "vendors", ["vendor_type"], unique=False)
    op.create_index("ix_vendors_npi", "vendors", ["npi"], unique=False)
    op.create_index("ix_vendors_status", "vendors", ["status"], unique=False)
    op.create_index("ix_vendors_created_by", "vendors", ["created_by"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_vendors_created_by", table_name="vendors")
    op.drop_index("ix_vendors_status", table_name="vendors")
    op.drop_index("ix_vendors_npi", table_name="vendors")
    op.drop_index("ix_vendors_vendor_type", table_name="vendors")
    op.drop_index("ix_vendors_name", table_name="vendors")
    op.drop_index("ix_vendors_tenant_npi", table_name="vendors")
    op.drop_index("ix_vendors_tenant_type", table_name="vendors")
    op.drop_index("ix_vendors_tenant_name", table_name="vendors")
    op.drop_index("ix_vendors_tenant_status", table_name="vendors")
    op.drop_index("ix_vendors_tenant_id", table_name="vendors")
    op.drop_table("vendors")
