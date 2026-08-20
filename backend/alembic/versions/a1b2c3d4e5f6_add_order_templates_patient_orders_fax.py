"""add order templates, patient orders, and fax logs

Revision ID: a1b2c3d4e5f6
Revises: 3f8a1c92d4e6
Create Date: 2026-08-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "3f8a1c92d4e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------------------------------------------------------
    # ORDER TEMPLATES (reusable "packs" — Comfort Pack, Standard Admission Pack, etc.)
    # ---------------------------------------------------------
    op.create_table(
        "order_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_order_templates_tenant_id", "order_templates", ["tenant_id"], unique=False)

    op.create_table(
        "order_template_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_type", sa.String(length=32), nullable=False),
        sa.Column("sub_type", sa.String(length=32), nullable=False, server_default=sa.text("'NEW'")),
        sa.Column("order_text", sa.Text(), nullable=False),
        sa.Column("strength", sa.String(length=128), nullable=True),
        sa.Column("dosage", sa.String(length=128), nullable=True),
        sa.Column("route", sa.String(length=64), nullable=True),
        sa.Column("frequency", sa.String(length=128), nullable=True),
        sa.Column("indication", sa.String(length=255), nullable=True),
        sa.Column("quantity", sa.String(length=64), nullable=True),
        sa.Column("payer", sa.String(length=64), nullable=True),
        sa.Column("vendor", sa.String(length=128), nullable=True),
        sa.Column("administered_by", sa.String(length=64), nullable=True),
        sa.Column("special_instruction", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["template_id"], ["order_templates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_order_template_items_template_id", "order_template_items", ["template_id"], unique=False)

    # ---------------------------------------------------------
    # PATIENT ORDERS (DME / Supply / Lab / Treatment / Diet / Other)
    # ---------------------------------------------------------
    op.create_table(
        "patient_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_type", sa.String(length=32), nullable=False),
        sa.Column("sub_type", sa.String(length=32), nullable=False, server_default=sa.text("'NEW'")),
        sa.Column("order_text", sa.Text(), nullable=False),
        sa.Column("strength", sa.String(length=128), nullable=True),
        sa.Column("dosage", sa.String(length=128), nullable=True),
        sa.Column("route", sa.String(length=64), nullable=True),
        sa.Column("frequency", sa.String(length=128), nullable=True),
        sa.Column("indication", sa.String(length=255), nullable=True),
        sa.Column("quantity", sa.String(length=64), nullable=True),
        sa.Column("payer", sa.String(length=64), nullable=True),
        sa.Column("vendor", sa.String(length=128), nullable=True),
        sa.Column("administered_by", sa.String(length=64), nullable=True),
        sa.Column("special_instruction", sa.Text(), nullable=True),
        sa.Column("otc_off_market", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("stat_order", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("phone_order", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("stop_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'active'")),
        sa.Column("discontinued_at", sa.Date(), nullable=True),
        sa.Column("discontinued_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("discontinue_reason", sa.Text(), nullable=True),
        sa.Column("source_template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["discontinued_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["source_template_id"], ["order_templates.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_patient_orders_patient_id", "patient_orders", ["patient_id"], unique=False)
    op.create_index("ix_patient_orders_tenant_id", "patient_orders", ["tenant_id"], unique=False)
    op.create_index("ix_patient_orders_order_type", "patient_orders", ["order_type"], unique=False)
    op.create_index("ix_patient_orders_source_template_id", "patient_orders", ["source_template_id"], unique=False)
    op.create_index("ix_patient_orders_patient_type", "patient_orders", ["patient_id", "order_type"], unique=False)
    op.create_index("ix_patient_orders_patient_status", "patient_orders", ["patient_id", "status"], unique=False)

    # ---------------------------------------------------------
    # FAX LOGS
    # ---------------------------------------------------------
    op.create_table(
        "fax_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_type", sa.String(length=32), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("recipient_name", sa.String(length=255), nullable=False),
        sa.Column("recipient_fax_number", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'QUEUED'")),
        sa.Column("provider", sa.String(length=32), nullable=False, server_default=sa.text("'SIMULATED'")),
        sa.Column("provider_reference", sa.String(length=128), nullable=True),
        sa.Column("document_summary", sa.Text(), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fax_logs_patient_id", "fax_logs", ["patient_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_fax_logs_patient_id", table_name="fax_logs")
    op.drop_table("fax_logs")

    op.drop_index("ix_patient_orders_patient_status", table_name="patient_orders")
    op.drop_index("ix_patient_orders_patient_type", table_name="patient_orders")
    op.drop_index("ix_patient_orders_source_template_id", table_name="patient_orders")
    op.drop_index("ix_patient_orders_order_type", table_name="patient_orders")
    op.drop_index("ix_patient_orders_patient_id", table_name="patient_orders")
    op.drop_table("patient_orders")

    op.drop_index("ix_order_template_items_template_id", table_name="order_template_items")
    op.drop_table("order_template_items")

    op.drop_index("ix_order_templates_tenant_id", table_name="order_templates")
    op.drop_table("order_templates")
