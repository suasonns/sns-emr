"""add physician_orders table and ORDER_MD_APPROVAL task/completion enum values

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE cannot run inside the same transaction that
    # uses the new value, but it CAN run in its own auto-committed statement
    # ahead of the rest of this migration (Postgres 12+ allows this outside
    # an explicit multi-statement transaction block).
    op.execute("COMMIT")
    op.execute("ALTER TYPE tasktype ADD VALUE IF NOT EXISTS 'ORDER_MD_APPROVAL'")
    op.execute("ALTER TYPE completionreferencetype ADD VALUE IF NOT EXISTS 'PHYSICIAN_ORDER'")
    op.execute("BEGIN")

    op.create_table(
        "physician_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'DRAFT'")),
        sa.Column("order_text", sa.Text(), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False, server_default=sa.text("'WRITTEN'")),
        sa.Column("ordered_by_provider_name", sa.String(length=255), nullable=False),
        sa.Column("ordered_by_provider_role", sa.String(length=16), nullable=False),
        sa.Column("ordered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("prescriber_authenticated", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("phone_readback_confirmed", sa.Boolean(), nullable=True),
        sa.Column("signed_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signature_method", sa.String(length=32), nullable=True),
        sa.Column("signature_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cancel_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["signed_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["cancelled_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_physician_orders_tenant_id", "physician_orders", ["tenant_id"], unique=False)
    op.create_index("ix_physician_orders_patient_id", "physician_orders", ["patient_id"], unique=False)
    op.create_index("ix_physician_orders_status", "physician_orders", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_physician_orders_status", table_name="physician_orders")
    op.drop_index("ix_physician_orders_patient_id", table_name="physician_orders")
    op.drop_index("ix_physician_orders_tenant_id", table_name="physician_orders")
    op.drop_table("physician_orders")
    # Postgres cannot drop enum values; ORDER_MD_APPROVAL / PHYSICIAN_ORDER
    # remain defined in the enum type (harmless, matches existing project
    # convention of forward-only enum growth).
