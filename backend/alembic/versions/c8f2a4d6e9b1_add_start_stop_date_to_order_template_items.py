"""add start_date/stop_date to order_template_items

Revision ID: c8f2a4d6e9b1
Revises: 9d3f6b7c8a10
Create Date: 2026-08-24 00:00:00.000000

Every real HospiceMD physician-order form (Lab, Treatment, Other, Supply,
DME, Diet) carries a Start Date and Stop Date, confirmed via side-by-side
screenshot review against the live SNS Order Packs template builder. The
live per-patient "Add New Order" screen (physician_orders table) folds
these into its free-text order_text string, but the Order Pack template
builder persists structured columns per item, so start_date/stop_date need
real columns here to be captured and carried through template import.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c8f2a4d6e9b1"
down_revision = "9d3f6b7c8a10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("order_template_items", sa.Column("start_date", sa.Date(), nullable=True))
    op.add_column("order_template_items", sa.Column("stop_date", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("order_template_items", "stop_date")
    op.drop_column("order_template_items", "start_date")
