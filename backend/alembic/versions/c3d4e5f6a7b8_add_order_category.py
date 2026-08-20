"""add order_category to physician_orders (unify all Orders Hub order types under MD signature)

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "physician_orders",
        sa.Column("order_category", sa.String(length=32), nullable=False, server_default=sa.text("'OTHER'")),
    )
    op.create_index("ix_physician_orders_order_category", "physician_orders", ["order_category"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_physician_orders_order_category", table_name="physician_orders")
    op.drop_column("physician_orders", "order_category")
