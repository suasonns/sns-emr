"""add visit-frequency fields to physician_orders

Revision ID: f4a6d1e8b3c7
Revises: c8f2a4d6e9b1
Create Date: 2026-08-23 23:50:00.000000

Structured, optional visit-frequency fields for OTHER-category physician
orders (e.g. "SN 2x/week + 3 PRN", "Aide 3x/week"), added alongside the
existing free-text order_text (never replacing it) so the supervisory-visit
scheduling engine can compute due dates without parsing free text.
See session file visit_notes_scheduling_spec.md section 5.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "f4a6d1e8b3c7"
down_revision = "c8f2a4d6e9b1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("physician_orders", sa.Column("visit_frequency_discipline", sa.String(length=16), nullable=True))
    op.add_column("physician_orders", sa.Column("visit_frequency_per_week", sa.Integer(), nullable=True))
    op.add_column("physician_orders", sa.Column("visit_frequency_prn_count", sa.Integer(), nullable=True))
    op.add_column("physician_orders", sa.Column("visit_frequency_superseded_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(
        "ix_physician_orders_visit_frequency_discipline",
        "physician_orders",
        ["visit_frequency_discipline"],
    )


def downgrade() -> None:
    op.drop_index("ix_physician_orders_visit_frequency_discipline", table_name="physician_orders")
    op.drop_column("physician_orders", "visit_frequency_superseded_at")
    op.drop_column("physician_orders", "visit_frequency_prn_count")
    op.drop_column("physician_orders", "visit_frequency_per_week")
    op.drop_column("physician_orders", "visit_frequency_discipline")
