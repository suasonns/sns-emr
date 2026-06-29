"""add signature_hash to med_reconciliation_items

Revision ID: a00fd20fbd36
Revises: f398111d94ad
Create Date: 2026-06-26 01:24:45.521279

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "a00fd20fbd36"
down_revision = "f398111d94ad"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    columns = {col["name"] for col in inspector.get_columns("med_reconciliation_items")}
    indexes = {idx["name"] for idx in inspector.get_indexes("med_reconciliation_items")}

    if "signature_hash" not in columns:
        op.add_column(
            "med_reconciliation_items",
            sa.Column("signature_hash", sa.String(length=64), nullable=True),
        )

    if "ix_med_reconciliation_items_signature_hash" not in indexes:
        op.create_index(
            "ix_med_reconciliation_items_signature_hash",
            "med_reconciliation_items",
            ["signature_hash"],
            unique=False,
        )

    if "ix_med_reconciliation_items_patient_pending_signature" not in indexes:
        op.create_index(
            "ix_med_reconciliation_items_patient_pending_signature",
            "med_reconciliation_items",
            ["patient_id", "review_status", "signature_hash"],
            unique=False,
        )


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    indexes = {idx["name"] for idx in inspector.get_indexes("med_reconciliation_items")}
    columns = {col["name"] for col in inspector.get_columns("med_reconciliation_items")}

    if "ix_med_reconciliation_items_patient_pending_signature" in indexes:
        op.drop_index(
            "ix_med_reconciliation_items_patient_pending_signature",
            table_name="med_reconciliation_items",
        )

    if "ix_med_reconciliation_items_signature_hash" in indexes:
        op.drop_index(
            "ix_med_reconciliation_items_signature_hash",
            table_name="med_reconciliation_items",
        )

    if "signature_hash" in columns:
        op.drop_column("med_reconciliation_items", "signature_hash")