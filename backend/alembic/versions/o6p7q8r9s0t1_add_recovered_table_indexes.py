"""add indexes omitted by recovered table migrations

Revision ID: o6p7q8r9s0t1
Revises: n5o6p7q8r9s0
Create Date: 2026-08-20
"""

from alembic import op


revision = "o6p7q8r9s0t1"
down_revision = "n5o6p7q8r9s0"
branch_labels = None
depends_on = None


INDEXES = (
    ("ix_fax_logs_created_by", "fax_logs", ("created_by",)),
    ("ix_fax_logs_tenant_id", "fax_logs", ("tenant_id",)),
    ("ix_order_template_items_created_by", "order_template_items", ("created_by",)),
    ("ix_order_templates_created_by", "order_templates", ("created_by",)),
    ("ix_patient_allergies_created_by", "patient_allergies", ("created_by",)),
    ("ix_patient_orders_created_by", "patient_orders", ("created_by",)),
    ("ix_physician_orders_created_by", "physician_orders", ("created_by",)),
    ("ix_physicians_created_by", "physicians", ("created_by",)),
)


def upgrade() -> None:
    for index_name, table_name, columns in INDEXES:
        op.create_index(index_name, table_name, columns, unique=False)


def downgrade() -> None:
    for index_name, table_name, _ in reversed(INDEXES):
        op.drop_index(index_name, table_name=table_name)
